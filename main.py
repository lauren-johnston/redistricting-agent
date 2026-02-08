import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
import httpx
from loguru import logger

load_dotenv()

from form_filler import FormFiller
from geocoding import _geocode, _center_point, _bounding_box_area_sq_miles
from notion_backend import check_coi_requirement, save_submission
from line.llm_agent import ToolEnv, loopback_tool
from line.llm_agent import LlmAgent, LlmConfig, end_call
from line.voice_agent_app import AgentEnv, CallRequest, VoiceAgentApp

#  ANTHROPIC_API_KEY=your-key GOOGLE_MAPS_API_KEY=your-key uv run python main.py

FORM_PATH = Path(__file__).parent / "community_form.yaml"

DEMO_ANSWERS = {
    "consent": True,
    "caller_name": "Lauren James",
    "zipcode": "94110",
    "address": "24th and Mission",
    "community_name": "Mission District",
    "community_description": "Majority Latino, lots of churches",
    "key_places": "Mission Dolores Park, the school next to it, Mission St, 24th and Mission",
    "community_boundaries": "Bernal, SOMA, Hayes, Castro are neighboring. Market St is also a barrier",
    "cultural_interests": "Predominant Latino, immigration concerns, affordable housing, drug use, public transit",
    "economic_interests": "Poor, service industry, gentrification and unemployment concerns",
    "community_activities": "Lots of churches (e.g. on Mission St), public transit",
    "other_considerations": "no",
    "phone_number": "555-0000",
}

SYSTEM_PROMPT = """You are a friendly voice assistant helping people share their community of interest for the redistricting process.

# What is a Community of Interest?
A community of interest is a neighborhood or group of people with shared concerns, interests, or characteristics that should be kept together in a single district during redistricting. This could be based on geography, culture, economics, shared services, or other common bonds.

# Personality
Warm, curious, genuine, and patient. You're here to listen and help people articulate what makes their community special.

# Voice and tone
Speak like a thoughtful friend, not a formal assistant or government official.
Use contractions and casual phrasing—the way people actually talk.
Match the caller's energy: playful if they're playful, grounded if they're serious.
Show genuine interest: "Oh that's interesting" or "Tell me more about that."

# Response style
Keep responses to 1-2 sentences for most exchanges. This is a conversation, not a lecture.
Ask one question at a time—don't overwhelm with multiple questions.
Never use lists, bullet points, or structured formatting—speak in natural prose.
Never say "Great question!" or other hollow affirmations.

# Consent
The FIRST question is about consent. You MUST obtain consent before proceeding.
- If the caller says YES: record the answer and continue with the form.
- If the caller says NO or declines: say "No problem at all — thanks for calling in. Have a good one!" and immediately call end_call. Do NOT ask any further questions.
- If the caller is unsure: briefly explain that their info will be part of the public redistricting record and ask again. If they still decline, end the call politely.

# Handling common situations
Didn't catch something: "Sorry, I didn't catch that—could you say that again?"
Caller seems unsure how to describe location: "Think about the places you go regularly—your grocery store, school, park, or place of worship. What are some of those spots?"
Caller doesn't know what to share: "Just tell me about your neighborhood and what makes it special. What do you and your neighbors have in common?"
Caller is brief: Gently probe with follow-up questions to get richer detail.
Caller wants to skip an optional question: That's fine—record their answer as "skipped" and move on.

# Tools

## check_coi_requirement
Call this IMMEDIATELY after recording the zipcode answer.
Pass the zip code. This looks up whether the caller's state legally requires communities of interest in redistricting.
When the result comes back, weave it into the conversation naturally. For example:
- If required: "By the way, in [state], communities of interest are actually required to be taken into account during redistricting — so what you're sharing today really matters."
- If not required: "It's worth knowing that [state] doesn't formally require communities of interest in redistricting, but your input is still really valuable for making sure your community is represented."
Don't make it sound like a legal disclaimer — keep it conversational and encouraging.

## geocode_community
Call this IMMEDIATELY after recording the community_boundaries answer.
Pass in the address, zip_code, key_places, and boundary_description you've collected so far.
This runs in the background—keep the conversation going while it processes.
When the result comes back, naturally read the geographic summary to the caller:
- "So it sounds like your community covers about X square miles around [area], bounded by [landmarks]—does that sound right?"
If they correct something, note it and move on.

## save_to_notion
Call this AFTER the user confirms the summary and BEFORE calling end_call.
No arguments needed — it automatically saves all form answers and geographic data.
Keep chatting naturally while it saves.

## run_demo
If the caller says "demo", "run demo", "skip to demo", or "demo mode" at ANY point, call this immediately.
It autopopulates the form with sample data about the Mission District in San Francisco, runs geocoding, and saves to Notion.
After it completes, read back the summary naturally and then call end_call.

## end_call
Use after save_to_notion completes AND the caller confirms the summary, OR if the caller declines consent.

Process (normal completion):
1. Summarize all the community information you've collected, including the geographic details
2. Ask if everything sounds right
3. Call save_to_notion (no arguments needed)
4. Say a natural goodbye: "Thanks so much for sharing about your community—this really helps!"
5. Then call end_call

Process (consent declined):
1. Thank them for calling
2. Call end_call immediately (do NOT call save_to_notion)"""


async def get_agent(env: AgentEnv, call_request: CallRequest):
    logger.info(f"Starting community form call: {call_request.call_id}")

    form = FormFiller(str(FORM_PATH), system_prompt=SYSTEM_PROMPT)

    # Shared dict for geocoding results — written by geocode_community, read by save_to_notion
    geo_data: dict = {}

    @loopback_tool(is_background=True)
    async def geocode_community(
        ctx: ToolEnv,
        address: Annotated[str, "The caller's address or nearest intersection"],
        zip_code: Annotated[str, "The caller's zip code"],
        boundary_description: Annotated[
            str,
            "The caller's verbal description of their community boundaries",
        ],
        key_places: Annotated[
            str,
            "Key places the caller mentioned (grocery stores, parks, schools, etc.)",
        ],
    ):
        """Geocode the caller's community boundaries to get geographic coordinates.
        Call this AFTER recording the community_boundaries answer."""
        yield "Looking up the geographic details for your community now..."

        all_points: list[dict] = []
        geocoded_landmarks: list[str] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            primary = await _geocode(client, f"{address}, {zip_code}")
            if primary:
                all_points.append(primary)

            boundary_parts = [
                part.strip()
                for part in boundary_description.replace(" and ", ", ")
                .replace(" to ", ", ")
                .replace(";", ",")
                .split(",")
                if part.strip() and len(part.strip()) > 2
            ]
            for landmark in boundary_parts[:6]:
                geo = await _geocode(client, f"{landmark}, {zip_code}")
                if geo:
                    all_points.append(geo)
                    geocoded_landmarks.append(f"{landmark} ({geo['formatted_address']})")

            place_parts = [
                part.strip()
                for part in key_places.replace(" and ", ", ")
                .replace(";", ",")
                .split(",")
                if part.strip() and len(part.strip()) > 2
            ]
            for place in place_parts[:4]:
                geo = await _geocode(client, f"{place}, {zip_code}")
                if geo:
                    all_points.append(geo)

        if not all_points:
            yield (
                "I wasn't able to pinpoint the exact location from the description. "
                "That's okay though — the verbal description you gave is still really valuable."
            )
            return

        import json
        center = _center_point(all_points)
        area = _bounding_box_area_sq_miles(all_points)

        summary_parts = []
        if primary:
            summary_parts.append(f"Centered around {primary['formatted_address']}")
        if area > 0:
            summary_parts.append(f"roughly {area} square miles")
        if geocoded_landmarks:
            summary_parts.append(f"bounded by {', '.join(geocoded_landmarks[:4])}")

        geographic_summary = " — ".join(summary_parts) if summary_parts else "Location identified"

        # Store geo results so save_to_notion can access them directly
        coords = [{"lat": p["lat"], "lng": p["lng"], "formatted_address": p["formatted_address"]} for p in all_points]
        geo_data["geographic_summary"] = geographic_summary
        geo_data["primary_address"] = primary["formatted_address"] if primary else ""
        geo_data["geocoded_landmarks"] = "; ".join(geocoded_landmarks)
        geo_data["all_coordinates"] = json.dumps(coords)

        logger.info(f"Geocoding complete, stored {len(coords)} coordinates")

        yield (
            f"Geographic summary: {geographic_summary}. "
            f"I mapped {len(all_points)} locations from your description. "
            "Read this summary back to the caller naturally and ask if it sounds like "
            "the right area. If they correct anything, note it but continue with the form."
        )

    @loopback_tool(is_background=True)
    async def run_demo(ctx: ToolEnv):
        """Run a demo with sample Mission District data. Call this when the caller says 'demo' or 'run demo'.
        This autopopulates the form, geocodes, and saves to Notion. No arguments needed."""
        import json

        yield "Running the demo now — one moment while I set everything up."

        # Populate form answers
        for key, value in DEMO_ANSWERS.items():
            form._answers[key] = value
        form._current_index = len(form._questions)
        logger.info(f"Demo: populated {len(DEMO_ANSWERS)} answers")

        # Run geocoding
        all_points: list[dict] = []
        geocoded_landmarks: list[str] = []
        zip_code = DEMO_ANSWERS["zipcode"]
        address = DEMO_ANSWERS["address"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            primary = await _geocode(client, f"{address}, {zip_code}")
            if primary:
                all_points.append(primary)

            for landmark in ["Market St", "Bernal Heights", "SOMA", "Castro"]:
                geo = await _geocode(client, f"{landmark}, {zip_code}")
                if geo:
                    all_points.append(geo)
                    geocoded_landmarks.append(f"{landmark} ({geo['formatted_address']})")

            for place in ["Mission Dolores Park", "24th and Mission"]:
                geo = await _geocode(client, f"{place}, {zip_code}")
                if geo:
                    all_points.append(geo)

        geographic_summary = "Location identified"
        if all_points:
            area = _bounding_box_area_sq_miles(all_points)
            summary_parts = []
            if primary:
                summary_parts.append(f"Centered around {primary['formatted_address']}")
            if area > 0:
                summary_parts.append(f"roughly {area} square miles")
            if geocoded_landmarks:
                summary_parts.append(f"bounded by {', '.join(geocoded_landmarks[:4])}")
            geographic_summary = " — ".join(summary_parts) if summary_parts else geographic_summary

            coords = [{"lat": p["lat"], "lng": p["lng"], "formatted_address": p["formatted_address"]} for p in all_points]
            geo_data["geographic_summary"] = geographic_summary
            geo_data["primary_address"] = primary["formatted_address"] if primary else ""
            geo_data["geocoded_landmarks"] = "; ".join(geocoded_landmarks)
            geo_data["all_coordinates"] = json.dumps(coords)
            logger.info(f"Demo: geocoded {len(coords)} points")

        # Save to Notion
        answers = dict(form._answers)
        answers.update(geo_data)
        result = await save_submission(answers)

        yield (
            f"Demo complete! {result}. "
            f"Submitted for Lauren James from the Mission District (94110). "
            f"Community is majority Latino with churches. "
            f"{geographic_summary}. "
            "Summarize this to the caller naturally and then call end_call."
        )

    @loopback_tool(is_background=True)
    async def save_to_notion(
        ctx: ToolEnv,
    ):
        """Save the completed community of interest form to the Notion database.
        Call this AFTER the user confirms the summary and BEFORE calling end_call.
        No arguments needed — form answers and geo data are saved automatically."""
        yield "Saving your submission now..."

        # Combine form answers + geo data
        answers = dict(form._answers)
        answers.update(geo_data)

        result = await save_submission(answers)
        yield result

    first_question = form.get_current_question_text()

    return LlmAgent(
        model="anthropic/claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        tools=[form.record_answer_tool, geocode_community, check_coi_requirement, save_to_notion, run_demo, end_call],
        config=LlmConfig(
            system_prompt=form.get_system_prompt(),
            introduction=f"Hi! Thanks for calling in. I'm here to help you share information about your community for the redistricting process. It'll just take a few minutes. {first_question}",
            max_tokens=4096,
        ),
    )


app = VoiceAgentApp(get_agent=get_agent)

if __name__ == "__main__":
    print("Starting app")
    app.run()

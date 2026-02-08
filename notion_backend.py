"""
Notion backend - saves completed community of interest form submissions to a Notion database.

Creates the database automatically on first run if it doesn't exist.
"""

import os
from typing import Annotated

import httpx
from loguru import logger

from line.llm_agent import ToolEnv, loopback_tool

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Stored after first creation so we don't recreate each time
_database_id: str | None = None


def _headers() -> dict:
    token = os.getenv("NOTION_SECRET", "")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def _find_or_create_database() -> str:
    """Find existing 'Community of Interest Submissions' database.
    
    For now, you need to manually create a database in Notion with the name
    'Community of Interest Submissions' and the required properties.
    """
    global _database_id
    if _database_id:
        return _database_id

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Search for existing database
        resp = await client.post(
            f"{NOTION_API_URL}/search",
            headers=_headers(),
            json={
                "query": "Community of Interest Submissions",
                "filter": {"value": "database", "property": "object"},
            },
        )
        data = resp.json()
        if data.get("results"):
            _database_id = data["results"][0]["id"]
            logger.info(f"Found existing Notion database: {_database_id}")
            return _database_id
        
        # If no database found, raise an error with instructions
        raise Exception(
            "No 'Community of Interest Submissions' database found in Notion. "
            "Please create it manually in Notion with these properties:\n"
            "- Name (title)\n- Phone (phone number)\n- Zip Code (text)\n- Address (text)\n- Community Name (text)\n- Community Description (text)\n- Key Places (text)\n- Community Boundaries (text)\n- Cultural Interests (text)\n- Economic Interests (text)\n- Community Activities (text)\n- Other Considerations (text)\n- Consent (checkbox)"
        )


def _rich_text(value: str) -> dict:
    """Build a Notion rich_text property value."""
    # Notion rich_text content is capped at 2000 chars
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _build_geojson(answers: dict) -> str:
    """Build a GeoJSON Feature string from the collected coordinates."""
    import json
    import math

    coords_str = answers.get("all_coordinates", "")
    if not coords_str:
        return ""

    try:
        coordinates = json.loads(coords_str)
        if not coordinates or len(coordinates) < 3:
            return ""

        # Sort by angle from center to form proper polygon
        center_lat = sum(c["lat"] for c in coordinates) / len(coordinates)
        center_lng = sum(c["lng"] for c in coordinates) / len(coordinates)

        def angle(c):
            return math.atan2(c["lat"] - center_lat, c["lng"] - center_lng)

        sorted_coords = sorted(coordinates, key=angle)

        # Build GeoJSON Feature with polygon (closed ring)
        ring = [[c["lng"], c["lat"]] for c in sorted_coords]
        ring.append(ring[0])

        feature = {
            "type": "Feature",
            "properties": {
                "name": answers.get("community_name", ""),
                "caller": answers.get("caller_name", ""),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [ring],
            },
        }
        return json.dumps(feature)

    except Exception as e:
        logger.error(f"Error building GeoJSON: {e}")
        return ""


def _generate_static_map_url(answers: dict) -> str | None:
    """Generate a Google Maps Static API URL that renders a filled polygon image."""
    import json
    import math

    try:
        coords_str = answers.get("all_coordinates", "")
        if not coords_str:
            return None

        coordinates = json.loads(coords_str)
        if not coordinates or len(coordinates) < 3:
            return None

        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        if not api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set, skipping map image")
            return None

        # Sort coordinates by angle from center to form a proper polygon
        center_lat = sum(c["lat"] for c in coordinates) / len(coordinates)
        center_lng = sum(c["lng"] for c in coordinates) / len(coordinates)

        def angle(c):
            return math.atan2(c["lat"] - center_lat, c["lng"] - center_lng)

        sorted_coords = sorted(coordinates, key=angle)

        # Build path param: color:fill|lat,lng|lat,lng|...
        path_parts = [f"{c['lat']},{c['lng']}" for c in sorted_coords]
        # Close the polygon
        path_parts.append(path_parts[0])
        path_str = "|".join(path_parts)

        # Google Static Maps API — draws a filled polygon
        url = (
            "https://maps.googleapis.com/maps/api/staticmap?"
            f"size=600x400"
            f"&path=color:0x4285F4CC|fillcolor:0x4285F444|weight:2|{path_str}"
            f"&key={api_key}"
        )

        logger.info(f"Generated static map URL ({len(url)} chars)")
        return url

    except Exception as e:
        logger.error(f"Error generating static map URL: {e}")
        return None


async def save_submission(answers: dict) -> str:
    """Save a completed form submission to Notion. Returns the page URL or error."""
    try:
        db_id = await _find_or_create_database()

        properties = {
            "Name": {"title": [{"text": {"content": answers.get("caller_name", "Unknown")}}]},
            "Consent": {"checkbox": bool(answers.get("consent", False))},
            "Zip Code": _rich_text(answers.get("zipcode", "")),
            "Community Name": _rich_text(answers.get("community_name", "")),
            "Community Description": _rich_text(answers.get("community_description", "")),
            "Key Places": _rich_text(answers.get("key_places", "")),
            "Community Boundaries": _rich_text(answers.get("community_boundaries", "")),
            "Cultural Interests": _rich_text(answers.get("cultural_interests", "")),
            "Economic Interests": _rich_text(answers.get("economic_interests", "")),
            "Community Activities": _rich_text(answers.get("community_activities", "")),
            "Other Considerations": _rich_text(answers.get("other_considerations", "")),
            "Geographic Summary": _rich_text(answers.get("geographic_summary", "")),
            "Primary Address": _rich_text(answers.get("primary_address", "")),
            "Geocoded Landmarks": _rich_text(answers.get("geocoded_landmarks", "")),
            "All Coordinates": _rich_text(answers.get("all_coordinates", "")),
            "GeoJSON": _rich_text(_build_geojson(answers)),
        }

        # Phone number uses the dedicated phone_number property type
        phone = answers.get("phone_number", "")
        if phone:
            properties["Phone"] = {"phone_number": str(phone)}

        # Build page body with map image if we have coordinates
        children = []
        map_url = _generate_static_map_url(answers)
        if map_url:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Community Boundary Map"}}]
                },
            })
            children.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": map_url},
                },
            })

        page_payload = {
            "parent": {"database_id": db_id},
            "properties": properties,
        }
        if children:
            page_payload["children"] = children

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{NOTION_API_URL}/pages",
                headers=_headers(),
                json=page_payload,
            )
            data = resp.json()

            if "id" in data:
                url = data.get("url", "")
                logger.info(f"Saved submission to Notion: {data['id']} ({url})")
                return f"Saved to Notion successfully (ID: {data['id']})"
            else:
                error = data.get("message", str(data))
                logger.error(f"Notion API error: {error}")
                return f"Failed to save to Notion: {error}"

    except Exception as e:
        logger.error(f"Error saving to Notion: {e}")
        return f"Error saving to Notion: {e}"


def _get_redistricting_db_id() -> str:
    return os.getenv("REDISTRICTING_CRITERIA_DB_ID", "")

# Zipcode prefix → state mapping (first 3 digits)


def _init_zip_to_state():
    """Build zipcode-prefix-to-state mapping."""
    if _ZIP_TO_STATE:
        return
    # Ranges: (start, end, state)  — covers all US zip prefixes
    ranges = [
        ("005", "009", "Puerto Rico"), ("010", "027", "Massachusetts"),
        ("028", "029", "Rhode Island"), ("030", "038", "New Hampshire"),
        ("039", "049", "Maine"), ("050", "059", "Vermont"),
        ("060", "069", "Connecticut"), ("070", "089", "New Jersey"),
        ("100", "149", "New York"), ("150", "196", "Pennsylvania"),
        ("197", "199", "Delaware"), ("200", "205", "District of Columbia"),
        ("206", "219", "Maryland"), ("220", "246", "Virginia"),
        ("247", "268", "West Virginia"), ("270", "289", "North Carolina"),
        ("290", "299", "South Carolina"), ("300", "319", "Georgia"),
        ("320", "349", "Florida"), ("350", "369", "Alabama"),
        ("370", "385", "Tennessee"), ("386", "397", "Mississippi"),
        ("400", "427", "Kentucky"), ("430", "459", "Ohio"),
        ("460", "479", "Indiana"), ("480", "499", "Michigan"),
        ("500", "528", "Iowa"), ("530", "549", "Wisconsin"),
        ("550", "567", "Minnesota"), ("570", "577", "South Dakota"),
        ("580", "588", "North Dakota"), ("590", "599", "Montana"),
        ("600", "629", "Illinois"), ("630", "658", "Missouri"),
        ("660", "679", "Kansas"), ("680", "693", "Nebraska"),
        ("700", "714", "Louisiana"), ("716", "729", "Arkansas"),
        ("730", "749", "Oklahoma"), ("750", "799", "Texas"),
        ("800", "816", "Colorado"), ("820", "831", "Wyoming"),
        ("832", "838", "Idaho"), ("840", "847", "Utah"),
        ("850", "865", "Arizona"), ("870", "884", "New Mexico"),
        ("889", "898", "Nevada"), ("900", "961", "California"),
        ("962", "966", "Military"), ("967", "968", "Hawaii"),
        ("970", "979", "Oregon"), ("980", "994", "Washington"),
        ("995", "999", "Alaska"),
    ]
    for start, end, state in ranges:
        for prefix in range(int(start), int(end) + 1):
            _ZIP_TO_STATE[f"{prefix:03d}"] = state


def _zip_to_state(zipcode: str) -> str | None:
    """Convert a US zipcode to a state name."""
    _init_zip_to_state()
    clean = zipcode.strip().replace("-", "")[:5]
    if len(clean) < 3:
        return None
    return _ZIP_TO_STATE.get(clean[:3])


async def _lookup_coi_required(state: str) -> dict | None:
    """Query the 2020 Redistricting Criteria Notion DB for a state."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{NOTION_API_URL}/databases/{_get_redistricting_db_id()}/query",
            headers=_headers(),
            json={
                "filter": {
                    "property": "State",
                    "title": {"equals": state},
                },
            },
        )
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None

        props = results[0]["properties"]
        coi_required = props.get("Communities of Interest Required", {}).get("checkbox", False)
        notes_parts = props.get("Notes", {}).get("rich_text", [])
        notes = "".join(t.get("plain_text", "") for t in notes_parts)
        return {"state": state, "coi_required": coi_required, "notes": notes}


@loopback_tool(is_background=True)
async def check_coi_requirement(
    ctx: ToolEnv,
    zipcode: Annotated[str, "The caller's zip code"],
):
    """Look up whether the caller's state requires communities of interest
    in redistricting. Call this right after recording the zipcode answer."""
    state = _zip_to_state(zipcode)
    if not state:
        yield f"Could not determine state from zip code {zipcode}."
        return

    yield f"Looking up redistricting criteria for {state}..."

    result = await _lookup_coi_required(state)
    if result is None:
        yield f"State: {state}. Could not find redistricting criteria data for this state."
        return

    if result["coi_required"]:
        msg = (
            f"State: {state}. Communities of interest ARE required to be considered "
            f"in redistricting for this state."
        )
    else:
        msg = (
            f"State: {state}. Communities of interest are NOT formally required "
            f"in redistricting for this state, but the caller's input is still valuable."
        )

    if result["notes"]:
        msg += f" Notes: {result['notes']}"

    yield msg


@loopback_tool(is_background=True)
async def save_to_notion(
    ctx: ToolEnv,
    submission_json: Annotated[str, "JSON string of all collected form answers"],
):
    """Save the completed community of interest form to the Notion database.
    Call this AFTER the user confirms the summary and BEFORE calling end_call.
    Pass all the collected answers as a JSON string.
    """
    import json

    yield "Saving your submission now..."

    try:
        answers = json.loads(submission_json)
    except json.JSONDecodeError:
        yield "There was an issue saving, but don't worry — your information has been recorded."
        return

    result = await save_submission(answers)
    yield result

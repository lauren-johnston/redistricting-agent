"""
Supabase backend - saves completed community of interest form submissions to Supabase.

Replaces the Notion backend with Supabase for persistent storage.
"""

import json
import math
import os
from typing import Annotated

import httpx
from loguru import logger

from line.llm_agent import ToolEnv, loopback_tool

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def _headers() -> dict:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _build_geojson(answers: dict) -> dict | None:
    """Build a GeoJSON Feature dict from the collected coordinates."""
    coords_str = answers.get("all_coordinates", "")
    if not coords_str:
        return None

    try:
        if isinstance(coords_str, str):
            coordinates = json.loads(coords_str)
        else:
            coordinates = coords_str

        if not coordinates or len(coordinates) < 3:
            return None

        # Sort by angle from center to form proper polygon
        center_lat = sum(c["lat"] for c in coordinates) / len(coordinates)
        center_lng = sum(c["lng"] for c in coordinates) / len(coordinates)

        def angle(c):
            return math.atan2(c["lat"] - center_lat, c["lng"] - center_lng)

        sorted_coords = sorted(coordinates, key=angle)

        # Build GeoJSON Feature with polygon (closed ring)
        ring = [[c["lng"], c["lat"]] for c in sorted_coords]
        ring.append(ring[0])

        return {
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

    except Exception as e:
        logger.error(f"Error building GeoJSON: {e}")
        return None


def _generate_static_map_url(answers: dict) -> str | None:
    """Generate a Google Maps Static API URL that renders a filled polygon image."""
    try:
        coords_str = answers.get("all_coordinates", "")
        if not coords_str:
            return None

        if isinstance(coords_str, str):
            coordinates = json.loads(coords_str)
        else:
            coordinates = coords_str

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

        # Build path param
        path_parts = [f"{c['lat']},{c['lng']}" for c in sorted_coords]
        path_parts.append(path_parts[0])
        path_str = "|".join(path_parts)

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
    """Save a completed form submission to Supabase. Returns status message."""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return "Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment"

        # Parse coordinates from string to JSON if needed
        all_coordinates = answers.get("all_coordinates", "")
        if isinstance(all_coordinates, str) and all_coordinates:
            try:
                all_coordinates = json.loads(all_coordinates)
            except json.JSONDecodeError:
                all_coordinates = None
        elif not all_coordinates:
            all_coordinates = None

        geojson = _build_geojson(answers)
        map_url = _generate_static_map_url(answers)

        row = {
            "caller_name": answers.get("caller_name", "Unknown"),
            "phone_number": answers.get("phone_number", ""),
            "consent": bool(answers.get("consent", False)),
            "zipcode": answers.get("zipcode", ""),
            "address": answers.get("address", ""),
            "community_name": answers.get("community_name", ""),
            "community_description": answers.get("community_description", ""),
            "key_places": answers.get("key_places", ""),
            "community_boundaries": answers.get("community_boundaries", ""),
            "cultural_interests": answers.get("cultural_interests", ""),
            "economic_interests": answers.get("economic_interests", ""),
            "community_activities": answers.get("community_activities", ""),
            "other_considerations": answers.get("other_considerations", ""),
            "geographic_summary": answers.get("geographic_summary", ""),
            "primary_address": answers.get("primary_address", ""),
            "geocoded_landmarks": answers.get("geocoded_landmarks", ""),
            "all_coordinates": all_coordinates,
            "geojson": geojson,
            "map_image_url": map_url,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/submissions",
                headers=_headers(),
                json=row,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                row_id = data[0]["id"] if data else "unknown"
                logger.info(f"Saved submission to Supabase: {row_id}")
                return f"Saved successfully (ID: {row_id})"
            else:
                error = resp.text
                logger.error(f"Supabase API error: {resp.status_code} {error}")
                return f"Failed to save: {error}"

    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
        return f"Error saving: {e}"


# ============================================================
# Redistricting criteria lookup (replaces Notion DB query)
# ============================================================

# Zipcode prefix → state mapping (first 3 digits)
_ZIP_TO_STATE: dict[str, str] = {}


def _init_zip_to_state():
    """Build zipcode-prefix-to-state mapping."""
    if _ZIP_TO_STATE:
        return
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
    """Query the redistricting_criteria table in Supabase for a state."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase not configured for redistricting criteria lookup")
        return None

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/redistricting_criteria",
            headers=_headers(),
            params={"state": f"eq.{state}", "limit": "1"},
        )

        if resp.status_code != 200:
            logger.error(f"Supabase query error: {resp.status_code} {resp.text}")
            return None

        data = resp.json()
        if not data:
            return None

        row = data[0]
        return {
            "state": row["state"],
            "coi_required": row.get("coi_required", False),
            "notes": row.get("notes", ""),
        }


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

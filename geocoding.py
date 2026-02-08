"""
Geocoding tool - converts verbal community boundary descriptions into geographic data
using the Google Maps Geocoding API during a live voice call.
"""

import os
import math
from typing import Annotated

import httpx
from loguru import logger

from line.llm_agent import ToolEnv, loopback_tool

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


async def _geocode(client: httpx.AsyncClient, address: str) -> dict | None:
    """Geocode a single address string. Returns {lat, lng, formatted_address} or None."""
    try:
        resp = await client.get(
            GEOCODE_URL,
            params={"address": address, "key": GOOGLE_MAPS_API_KEY},
        )
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            loc = result["geometry"]["location"]
            return {
                "lat": loc["lat"],
                "lng": loc["lng"],
                "formatted_address": result["formatted_address"],
            }
    except Exception as e:
        logger.warning(f"Geocode failed for '{address}': {e}")
    return None


def _haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in miles."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bounding_box_area_sq_miles(points: list[dict]) -> float:
    """Rough area from bounding box of geocoded points."""
    if len(points) < 2:
        return 0.0
    lats = [p["lat"] for p in points]
    lngs = [p["lng"] for p in points]
    width = _haversine_miles(min(lats), min(lngs), min(lats), max(lngs))
    height = _haversine_miles(min(lats), min(lngs), max(lats), min(lngs))
    return round(width * height, 2)


def _center_point(points: list[dict]) -> dict:
    """Average lat/lng of a set of points."""
    avg_lat = sum(p["lat"] for p in points) / len(points)
    avg_lng = sum(p["lng"] for p in points) / len(points)
    return {"lat": round(avg_lat, 6), "lng": round(avg_lng, 6)}


@loopback_tool(is_background=True)
async def geocode_community(
    ctx: ToolEnv,
    address: Annotated[str, "The caller's address or nearest intersection"],
    zip_code: Annotated[str, "The caller's zip code"],
    boundary_description: Annotated[
        str,
        "The caller's verbal description of their community boundaries, including streets, landmarks, and natural features",
    ],
    key_places: Annotated[
        str,
        "Key places the caller mentioned (grocery stores, parks, schools, etc.)",
    ],
) -> str:
    """Geocode the caller's community boundaries to get geographic coordinates and area estimate.
    Call this AFTER recording the community_boundaries answer.
    The result will be read back to the caller for confirmation.
    """
    yield "Looking up the geographic details for your community now..."

    all_points: list[dict] = []
    geocoded_landmarks: list[str] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Geocode the primary address
        primary = await _geocode(client, f"{address}, {zip_code}")
        if primary:
            all_points.append(primary)
            logger.info(f"Primary address geocoded: {primary['formatted_address']}")

        # 2. Parse boundary landmarks and geocode each
        #    Split on common delimiters people use when describing boundaries
        boundary_parts = [
            part.strip()
            for part in boundary_description.replace(" and ", ", ")
            .replace(" to ", ", ")
            .replace(";", ",")
            .split(",")
            if part.strip() and len(part.strip()) > 2 and not part.strip().startswith("the ")
        ]

        for landmark in boundary_parts[:6]:  # cap at 6 to limit API calls
            geo = await _geocode(client, f"{landmark}, {zip_code}")
            if geo:
                all_points.append(geo)
                geocoded_landmarks.append(
                    f"{landmark} ({geo['formatted_address']})"
                )
                logger.info(f"Boundary landmark geocoded: {landmark} -> {geo['formatted_address']}")

        # 3. Geocode key community places
        place_parts = [
            part.strip()
            for part in key_places.replace(" and ", ", ")
            .replace(";", ",")
            .split(",")
            if part.strip() and len(part.strip()) > 2
        ]

        for place in place_parts[:4]:  # cap at 4
            geo = await _geocode(client, f"{place}, {zip_code}")
            if geo:
                all_points.append(geo)
                logger.info(f"Key place geocoded: {place} -> {geo['formatted_address']}")

    # Build result summary
    if not all_points:
        yield (
            "I wasn't able to pinpoint the exact location from the description. "
            "That's okay though — the verbal description you gave is still really valuable."
        )
        return

    center = _center_point(all_points)
    area = _bounding_box_area_sq_miles(all_points)

    summary_parts = []

    if primary:
        summary_parts.append(
            f"Centered around {primary['formatted_address']}"
        )

    if area > 0:
        summary_parts.append(f"roughly {area} square miles")

    if geocoded_landmarks:
        boundary_str = ", ".join(geocoded_landmarks[:4])
        summary_parts.append(f"bounded by {boundary_str}")

    geographic_summary = " — ".join(summary_parts) if summary_parts else "Location identified"

    result = {
        "center": center,
        "approximate_area_sq_miles": area,
        "num_points_geocoded": len(all_points),
        "geocoded_landmarks": geocoded_landmarks,
        "primary_address": primary["formatted_address"] if primary else None,
        "summary": geographic_summary,
    }

    logger.info(f"Geocoding complete: {result}")

    yield (
        f"Geographic summary: {geographic_summary}. "
        f"I mapped {len(all_points)} locations from your description. "
        "Read this summary back to the caller naturally and ask if it sounds like "
        "the right area. If they correct anything, note it but continue with the form."
    )

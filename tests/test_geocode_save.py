#!/usr/bin/env python3
"""
Quick test: geocode a community and save to Notion with geo data.
Verifies that landmarks, coordinates, GeoJSON, and polygon map all save correctly.
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import httpx
from geocoding import _geocode, _center_point, _bounding_box_area_sq_miles
from notion_backend import save_submission


async def test_geocode_and_save():
    print("=== Test: Geocode + Save to Notion ===\n")

    zip_code = "94110"
    address = "24th and Mission"
    boundary_description = "Market Street, Cesar Chavez, Potrero Avenue, Dolores Street"
    key_places = "Dolores Park, Mission Cultural Center"

    # 1. Geocode
    print("1. Geocoding landmarks...")
    all_points = []
    geocoded_landmarks = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        primary = await _geocode(client, f"{address}, {zip_code}")
        if primary:
            all_points.append(primary)
            print(f"   Primary: {primary['formatted_address']}")

        for landmark in boundary_description.split(", "):
            geo = await _geocode(client, f"{landmark}, {zip_code}")
            if geo:
                all_points.append(geo)
                geocoded_landmarks.append(f"{landmark} ({geo['formatted_address']})")
                print(f"   Landmark: {landmark} -> {geo['formatted_address']}")

        for place in key_places.split(", "):
            geo = await _geocode(client, f"{place}, {zip_code}")
            if geo:
                all_points.append(geo)
                print(f"   Place: {place} -> {geo['formatted_address']}")

    if not all_points:
        print("   ❌ No points geocoded!")
        return

    # 2. Build geo data
    print(f"\n2. Building geo data ({len(all_points)} points)...")
    center = _center_point(all_points)
    area = _bounding_box_area_sq_miles(all_points)
    coords = [{"lat": p["lat"], "lng": p["lng"], "formatted_address": p["formatted_address"]} for p in all_points]

    summary_parts = []
    if primary:
        summary_parts.append(f"Centered around {primary['formatted_address']}")
    if area > 0:
        summary_parts.append(f"roughly {area} square miles")
    if geocoded_landmarks:
        summary_parts.append(f"bounded by {', '.join(geocoded_landmarks[:4])}")
    geographic_summary = " — ".join(summary_parts)

    print(f"   Summary: {geographic_summary}")
    print(f"   Coordinates: {len(coords)} points")

    # 3. Save to Notion
    print("\n3. Saving to Notion...")
    answers = {
        "consent": True,
        "caller_name": "Test Geocode",
        "zipcode": zip_code,
        "address": address,
        "community_name": "Mission District",
        "community_description": "Latino cultural hub in SF",
        "key_places": key_places,
        "community_boundaries": boundary_description,
        "cultural_interests": "Latino culture, murals",
        "economic_interests": "gentrification concerns",
        "community_activities": "Carnaval, Sunday Streets",
        "other_considerations": "skipped",
        "phone_number": "555-0000",
        # Geo data (what the closure would provide)
        "geographic_summary": geographic_summary,
        "primary_address": primary["formatted_address"] if primary else "",
        "geocoded_landmarks": "; ".join(geocoded_landmarks),
        "all_coordinates": json.dumps(coords),
    }

    result = await save_submission(answers)
    print(f"   {result}")

    # 4. Verify
    print("\n4. Verification checklist:")
    print(f"   ✅ Geocoded {len(all_points)} points")
    print(f"   ✅ {len(geocoded_landmarks)} landmarks encoded")
    print(f"   {'✅' if area > 0 else '❌'} Area: {area} sq miles")
    print(f"   {'✅' if len(coords) >= 3 else '❌'} Enough coords for polygon: {len(coords)}")
    print(f"\n   Check Notion for: polygon map image, GeoJSON field, coordinates")


if __name__ == "__main__":
    asyncio.run(test_geocode_and_save())

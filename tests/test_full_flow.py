#!/usr/bin/env python3
"""
Test the full geocoding flow with realistic user input.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import httpx
from loguru import logger

# Copy the core geocoding functions
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

async def _geocode(client: httpx.AsyncClient, address: str) -> dict | None:
    """Geocode a single address string."""
    try:
        resp = await client.get(GEOCODE_URL, params={"address": address, "key": GOOGLE_MAPS_API_KEY})
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
    import math
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
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

async def test_realistic_scenario():
    """Test with realistic user input from the voice agent."""
    
    print("🎯 Testing realistic scenario...")
    
    # Simulate data collected from the form
    caller_data = {
        "address": "Mission and 24th",
        "zip_code": "94110",
        "boundary_description": "Market Street to the north, Dolores Street to the east, 24th Street to the south, Church Street to the west",
        "key_places": "Dolores Park, Mission High School, Bi-Rite Market"
    }
    
    print(f"Input data: {caller_data}")
    
    all_points: list[dict] = []
    geocoded_landmarks: list[str] = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Geocode primary address with zip context
        primary_query = f"{caller_data['address']}, {caller_data['zip_code']}"
        print(f"Trying to geocode: '{primary_query}'")
        primary = await _geocode(client, primary_query)
        if primary:
            all_points.append(primary)
            print(f"✅ Primary: {primary['formatted_address']}")
        else:
            print(f"❌ Primary failed for: {primary_query}")
            # Try with city context
            city_query = f"{caller_data['address']}, San Francisco, CA"
            print(f"Trying city context: '{city_query}'")
            primary = await _geocode(client, city_query)
            if primary:
                all_points.append(primary)
                print(f"✅ Primary (city): {primary['formatted_address']}")
            else:
                print(f"❌ Primary failed completely")
        
        # 2. Parse and geocode boundaries
        boundary_parts = [
            part.strip()
            for part in caller_data['boundary_description'].replace(" to ", ", ")
            .replace(" and ", ", ")
            .replace(";", ",")
            .split(",")
            if part.strip() and len(part.strip()) > 2
        ]
        
        print(f"Boundary landmarks to geocode: {boundary_parts}")
        
        for landmark in boundary_parts[:6]:
            query = f"{landmark}, San Francisco, CA"  # Add city context
            geo = await _geocode(client, query)
            if geo:
                all_points.append(geo)
                geocoded_landmarks.append(f"{landmark} ({geo['formatted_address']})")
                print(f"✅ Boundary: {landmark} -> {geo['formatted_address']}")
            else:
                print(f"❌ Boundary failed: {landmark}")
        
        # 3. Geocode key places
        place_parts = [
            part.strip()
            for part in caller_data['key_places'].replace(" and ", ", ")
            .replace(";", ",")
            .split(",")
            if part.strip() and len(part.strip()) > 2
        ]
        
        print(f"Key places to geocode: {place_parts}")
        
        for place in place_parts[:4]:
            query = f"{place}, San Francisco, CA"
            geo = await _geocode(client, query)
            if geo:
                all_points.append(geo)
                print(f"✅ Place: {place} -> {geo['formatted_address']}")
            else:
                print(f"❌ Place failed: {place}")
    
    # Calculate summary
    if not all_points:
        print("❌ No points geocoded successfully")
        return
    
    # Center point
    center_lat = sum(p["lat"] for p in all_points) / len(all_points)
    center_lng = sum(p["lng"] for p in all_points) / len(all_points)
    center = {"lat": round(center_lat, 6), "lng": round(center_lng, 6)}
    
    # Area
    area = _bounding_box_area_sq_miles(all_points)
    
    print(f"\n📊 Results:")
    print(f"   Total points geocoded: {len(all_points)}")
    print(f"   Center point: {center}")
    print(f"   Approximate area: {area} square miles")
    print(f"   Primary address: {primary['formatted_address'] if primary else 'None'}")
    print(f"   Boundary landmarks: {len(geocoded_landmarks)}")
    
    # Generate natural language summary
    summary_parts = []
    if primary:
        summary_parts.append(f"Centered around {primary['formatted_address']}")
    if area > 0:
        summary_parts.append(f"roughly {area} square miles")
    if geocoded_landmarks:
        boundary_str = ", ".join(geocoded_landmarks[:3])
        summary_parts.append(f"bounded by {boundary_str}")
    
    geographic_summary = " — ".join(summary_parts)
    print(f"\n🗣️ Voice summary: '{geographic_summary}'")

if __name__ == "__main__":
    asyncio.run(test_realistic_scenario())

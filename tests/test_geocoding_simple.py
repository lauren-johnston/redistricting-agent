#!/usr/bin/env python3
"""
Simple test of the geocoding logic without the Line SDK decorators.
"""

import asyncio
import os
import httpx
from loguru import logger

# Copy the core geocoding functions here for testing
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

async def _geocode(client: httpx.AsyncClient, address: str) -> dict | None:
    """Geocode a single address string. Returns {lat, lng, formatted_address} or None."""
    try:
        params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
        print(f"   Request URL: {GEOCODE_URL}")
        print(f"   Params: {params}")
        
        resp = await client.get(GEOCODE_URL, params=params)
        data = resp.json()
        
        print(f"   Response status: {data.get('status')}")
        if data.get("error_message"):
            print(f"   Error message: {data.get('error_message')}")
        
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
        print(f"   Exception: {e}")
    return None

async def test_primary_address():
    """Test just the primary address geocoding."""
    
    # Set API key
    os.environ["GOOGLE_MAPS_API_KEY"] = "os.getenv("GOOGLE_MAPS_API_KEY")"
    
    print("🧪 Testing primary address geocoding...")
    
    test_cases = [
        "19th and Valencia, San Francisco",
        "19th and Valencia",
        "19th and Valencia, 94110",
        "Mission and 24th, San Francisco",
        "Castro and Market, San Francisco"
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for address in test_cases:
            print(f"\n--- Testing: '{address}' ---")
            result = await _geocode(client, address)
            if result:
                print(f"✅ SUCCESS: {result['formatted_address']}")
                print(f"   Coordinates: {result['lat']}, {result['lng']}")
            else:
                print(f"❌ FAILED: Could not geocode")

async def test_boundary_landmarks():
    """Test geocoding common boundary landmarks."""
    
    print("\n🧪 Testing boundary landmarks...")
    
    landmarks = [
        "Market Street, San Francisco",
        "Dolores Street, San Francisco", 
        "24th Street, San Francisco",
        "Church Street, San Francisco",
        "Dolores Park, San Francisco",
        "Mission High School, San Francisco"
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for landmark in landmarks:
            print(f"\n--- Testing: '{landmark}' ---")
            result = await _geocode(client, landmark)
            if result:
                print(f"✅ SUCCESS: {result['formatted_address']}")
                print(f"   Coordinates: {result['lat']}, {result['lng']}")
            else:
                print(f"❌ FAILED: Could not geocode")

if __name__ == "__main__":
    asyncio.run(test_primary_address())
    asyncio.run(test_boundary_landmarks())

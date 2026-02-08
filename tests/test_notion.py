#!/usr/bin/env python3
"""
Quick test of the Notion integration.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from notion_backend import save_submission, _find_or_create_database


async def test_notion():
    print("Testing Notion integration...")
    
    # Check environment
    token = os.getenv("NOTION_SECRET")
    if not token:
        print("❌ NOTION_SECRET not found in environment")
        return
    
    print(f"✅ Found NOTION_SECRET: {token[:10]}...")
    
    # Test database creation/finding
    try:
        db_id = await _find_or_create_database()
        print(f"✅ Database ID: {db_id}")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return
    
    # Test saving a sample submission
    test_answers = {
        "consent": True,
        "caller_name": "Test User",
        "zipcode": "12345",
        "community_name": "Test Community",
        "community_description": "A test community for integration testing.",
        "key_places": "Test park, test store",
        "community_boundaries": "Test street to test avenue",
        "cultural_interests": "Test culture",
        "economic_interests": "Test economy",
        "community_activities": "Test activities",
        "other_considerations": "Test considerations",
        "phone_number": "555-1234",
        # Geographic data from geocoding
        "geographic_summary": "Centered around 123 Test St — roughly 2.5 square miles — bounded by Test Street, Test Avenue",
        "primary_address": "123 Test St, Test City, 12345",
        "geocoded_landmarks": "Test Street (123 Test St); Test Avenue (456 Test Ave); Test Park (789 Park Rd)",
        "all_coordinates": '[{"lat": 40.7128, "lng": -74.0060, "formatted_address": "123 Test St, Test City, 12345"}, {"lat": 40.7135, "lng": -74.0070, "formatted_address": "456 Test Ave, Test City, 12345"}, {"lat": 40.7140, "lng": -74.0080, "formatted_address": "789 Park Rd, Test City, 12345"}]'
    }
    
    try:
        result = await save_submission(test_answers)
        print(f"✅ Save result: {result}")
    except Exception as e:
        print(f"❌ Save failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_notion())

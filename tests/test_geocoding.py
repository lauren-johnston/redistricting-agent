#!/usr/bin/env python3
"""
Quick test script for geocoding functionality without the full voice agent.
"""

import asyncio
import os
from pathlib import Path

# Add the project root to Python path so we can import modules
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

from geocoding import geocode_community
# Access the actual function from the decorated tool
geocode_fn = geocode_community.fn

async def test_geocoding():
    """Test the geocoding tool with sample data."""
    
    # Set environment variables for testing
    os.environ["GOOGLE_MAPS_API_KEY"] = "os.getenv("GOOGLE_MAPS_API_KEY")"
    
    print("🧪 Testing geocoding tool...")
    
    # Test case 1: Clear intersection
    print("\n--- Test 1: Clear intersection ---")
    test_data_1 = {
        "address": "19th and Valencia, San Francisco",
        "zip_code": "94110", 
        "boundary_description": "Market Street to the north, Dolores Street to the east, 24th Street to the south, Church Street to the west",
        "key_places": "Dolores Park, Mission High School, Bi-Rite Market"
    }
    
    print(f"Input: {test_data_1}")
    
    # Mock ToolEnv for testing
    class MockToolEnv:
        class TurnEnv:
            pass
        turn_env = TurnEnv()
    
    ctx = MockToolEnv()
    
    # Call the geocoding tool
    async for result in geocode_fn(
        ctx=ctx,
        address=test_data_1["address"],
        zip_code=test_data_1["zip_code"],
        boundary_description=test_data_1["boundary_description"],
        key_places=test_data_1["key_places"]
    ):
        print(f"Result: {result}")
    
    # Test case 2: Vague address (should fail gracefully)
    print("\n--- Test 2: Vague address ---")
    test_data_2 = {
        "address": "somewhere in the mission",
        "zip_code": "94110",
        "boundary_description": "around there somewhere",
        "key_places": "that one park"
    }
    
    print(f"Input: {test_data_2}")
    
    async for result in geocode_fn(
        ctx=ctx,
        address=test_data_2["address"],
        zip_code=test_data_2["zip_code"],
        boundary_description=test_data_2["boundary_description"],
        key_places=test_data_2["key_places"]
    ):
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_geocoding())

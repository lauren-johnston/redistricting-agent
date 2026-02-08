# Tests

This folder contains test scripts for the redistricting agent.

## Test Files

- `test_geocoding_simple.py` - Basic geocoding functionality test
- `test_full_flow.py` - End-to-end test with realistic user input
- `test_geocoding.py` - Original test (deprecated)

## Running Tests

```bash
# Set your API key
export GOOGLE_MAPS_API_KEY=your-key

# Run individual tests
uv run python tests/test_geocoding_simple.py
uv run python tests/test_full_flow.py

# Or run with inline key
GOOGLE_MAPS_API_KEY=your-key uv run python tests/test_full_flow.py
```

## What They Test

- Primary address geocoding (intersections, addresses)
- Boundary landmark parsing and geocoding
- Key place geocoding (parks, schools, businesses)
- Area calculation and center point computation
- Natural language summary generation

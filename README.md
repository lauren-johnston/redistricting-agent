# Redistricting Voice Agent

Gathering data about how people define their community is a critical step in the redistricting process. In 2019, I cofounded the Representable.org project in partnership with Princeton's Electoral Innovation Lab. We had people draw their community on a map with MapBox and type in the info about their community.

Although this tool was used successfully in several states during the 2020 redistricting cycle, the fact that people had to have access to a laptop, a fast internet connection, and the willingness to create an account and hand-draw their community made it inaccessible to the broader public.

In 2026, realistic voice agents with tool calling have made it possible to collect community data from the public with only a phone call. For the next redistricting cycle, we want everyone to be able to contribute.

# How to use

## Prequisites

1. Sign up for a Cartesia account at [Cartesia](https://cartesia.ai) and create a voice agent and link to Github in settings. Then, clone the repo for that agent locally.
2. Sign up for an Anthropic developer account and get an API key at [Anthropic](https://console.anthropic.com/api-keys).

## Instructions

1. Install the Cartesia CLI and `uv` to manage dependencies and virtual environments.

```bash
curl -fsSL https://cartesia.sh | sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a [Cartesia API key](https://play.cartesia.ai/keys). You will need this in the next step.
3. Get a [Google Maps API key](https://console.cloud.google.com/apis/credentials) and enable the "Geocoding API".
4. Set up Notion: Create a "Community of Interest Submissions" database and get your Notion secret and database ID (see `NOTION_SETUP.md`).
5. Authenticate into Cartesia and initialize a project. You can link this project to an agent you created.

```jsx
cartesia auth login
cartesia init
```

6. Start your agent server.

```bash
uv sync
ANTHROPIC_API_KEY=your-anthropic-key GOOGLE_MAPS_API_KEY=your-google-maps-key NOTION_SECRET=your-notion-secret NOTION_SUBMISSIONS_DB_ID=your-db-id REDISTRICTING_CRITERIA_DB_ID=your-criteria-db-id PORT=8000 uv run python main.py
```

7. In a separate terminal, chat with your agent by simply running:

```bash
cartesia chat 8000 # test your agent's reasoning in text
```

8. Commit your changes to `main` and `git push`. Cartesia will auto-deploy your `main` branch.

## Testing

The project includes test scripts for validating the geocoding functionality:

```bash
# Set your API key
export GOOGLE_MAPS_API_KEY=your-key

# Run geocoding tests
uv run python tests/test_geocoding_simple.py
uv run python tests/test_full_flow.py

# Or run with inline key
GOOGLE_MAPS_API_KEY=your-key uv run python tests/test_full_flow.py
```

See `tests/README.md` for detailed testing information.

# Quick Reference

## Redistricting Basics
- **Main districts**: Congressional, State Senate, State House (redrawn every 10 years)
- **Goal**: Keep communities of interest together in single districts
- **Problem**: Gerrymandering splits communities for political advantage
- **Solution**: Collect community data to challenge unfair maps

## Agent Workflow
1. Collect caller name (optional) and zipcode
2. Get community name and description
3. Gather location data (key places, boundaries)
4. Document cultural, economic, and social interests
5. Capture other considerations for redistricting

## Data Storage
All submissions are stored in Notion with:
- Form answers (community details, cultural/economic interests)
- Geocoded coordinates and landmarks
- Polygon map image (Google Static Maps)
- GeoJSON for boundary visualization

## Future Integration
- **District lookup**: Show current districts by zipcode

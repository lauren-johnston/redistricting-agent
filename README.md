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
3. Authenticate into Cartesia and initialize a project. You can link this project to an agent you created.

```jsx
cartesia auth login
cartesia init
```

4. Start your agent server.

```bash
uv sync
ANTHROPIC_API_KEY=your-api-key PORT=8000 uv run python main.py
```

5. In a separate terminal, chat with your agent by simply running:

```bash
cartesia chat 8000 # test your agent's reasoning in text
```

6. Commit your changes to `main` and `git push`. Cartesia will auto-deploy your `main` branch.

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

## Future Integration
- **Database**: Store form submissions (Supabase recommended)
- **Mapping**: Convert verbal descriptions to polygons (Google Maps)
- **District lookup**: Show current districts by zipcode
- **Census blocks**: Paint tool for precise boundaries
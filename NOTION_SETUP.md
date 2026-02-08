# Notion Setup Instructions

## Quick Setup

1. **Create a page in Notion** (any page will work as a parent)
2. **Create the database** with this exact structure:

### Database Name
`Community of Interest Submissions`

### Properties (create in this order)
- **Name** → Title
- **Phone** → Phone number  
- **Zip Code** → Text
- **Community Name** → Text
- **Community Description** → Text
- **Key Places** → Text
- **Community Boundaries** → Text
- **Cultural Interests** → Text
- **Economic Interests** → Text
- **Community Activities** → Text
- **Other Considerations** → Text
- **Geographic Summary** → Text
- **Primary Address** → Text
- **Geocoded Landmarks** → Text
- **All Coordinates** → Text
- **GeoJSON** → Text
- **Consent** → Checkbox

## Test the Integration

Once the database is created, run:
```bash
uv run python tests/test_notion.py
```

This will test the connection and save a sample submission.

## How it Works

- The voice agent collects all form answers
- When the user confirms the summary, it calls `save_to_notion`
- The submission is saved as a new page in your Notion database
- All data is stored securely in your Notion workspace

## Security

- The Notion secret is stored in `.env` (never committed to git)
- The integration only has access to create pages in the specified database
- No other Notion data is accessed

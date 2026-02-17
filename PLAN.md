[x] Update prompt to be more specific to the redistricting process
[x] Convert to form filler pattern (YAML-driven questionnaire)
[x] Add Google Maps geocoding tool to convert verbal boundary descriptions into geographic data during the call
[x] Replace Notion backend with Supabase (supabase_backend.py, supabase_schema.sql)
[x] Build Next.js dashboard (web/) with table view, map view, and detail panel
[x] Convert geocoded points into proper map polygons (GeoJSON stored in Supabase JSONB)


# Future work (don't implement now)
[ ] Add an audit log of the LLM convo so that we can review if needed
[ ] Deploy dashboard to Vercel
[ ] Seed redistricting_criteria table with all 50 states
[ ] Figure out how to look up redistricting data for each state to give the user information about the redistricting process
# Quick Setup Guide

## 1. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to the **SQL Editor** and run the contents of `supabase_schema.sql`
3. Go to **Settings → API** and copy:
   - **Project URL** (e.g., `https://abcdefgh.supabase.co`)
   - **service_role key** (for the Python backend)
   - **anon/public key** (for the Next.js dashboard)

## 2. Voice Agent Setup

Add to your `.env` file:

```bash
# Existing
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_MAPS_API_KEY=your-google-maps-key

# New - Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

Then run:

```bash
uv sync
PORT=8000 uv run python main.py
```

## 3. Dashboard Setup

```bash
cd web
cp .env.local.example .env.local
```

Edit `web/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Run locally:

```bash
npm run dev
# Visit http://localhost:3000
```

## 4. Deploy Dashboard to Vercel

1. Push your repo to GitHub
2. Go to [vercel.com](https://vercel.com) and import your project
3. Set **Root Directory** to `web`
4. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy

## 5. Seed Redistricting Criteria (Optional)

To enable the `check_coi_requirement` tool, you need to populate the `redistricting_criteria` table. Run this in the Supabase SQL Editor:

```sql
INSERT INTO redistricting_criteria (state, coi_required, notes) VALUES
  ('California', true, 'Required by Prop 11 (2008) and Prop 20 (2010)'),
  ('New York', false, 'Not formally required'),
  ('Texas', false, 'Not formally required'),
  ('Florida', false, 'Not formally required')
  -- Add more states as needed
ON CONFLICT (state) DO NOTHING;
```

## Testing

Test geocoding:
```bash
GOOGLE_MAPS_API_KEY=your-key uv run python tests/test_geocoding_simple.py
```

Test full flow (geocode + save to Supabase):
```bash
uv run python tests/test_geocode_save.py
```

Test voice agent in text mode:
```bash
cartesia chat 8000
```

-- Supabase schema for Redistricting Agent
-- Run this in the Supabase SQL Editor to set up your tables.

-- Enable PostGIS for geographic data (optional but recommended)
-- create extension if not exists postgis;

-- ============================================================
-- Table: submissions
-- Stores community-of-interest form submissions from voice calls
-- ============================================================
create table if not exists submissions (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now() not null,

  -- Caller info
  caller_name text,
  phone_number text,
  consent boolean default false not null,
  zipcode text,
  address text,

  -- Community info
  community_name text,
  community_description text,
  key_places text,
  community_boundaries text,
  cultural_interests text,
  economic_interests text,
  community_activities text,
  other_considerations text,

  -- Geographic data (from geocoding)
  geographic_summary text,
  primary_address text,
  geocoded_landmarks text,
  all_coordinates jsonb,       -- array of {lat, lng, formatted_address}
  geojson jsonb,               -- GeoJSON Feature with polygon
  map_image_url text           -- Google Static Maps URL
);

-- ============================================================
-- Table: redistricting_criteria
-- Lookup table: whether each state requires COI in redistricting
-- ============================================================
create table if not exists redistricting_criteria (
  id uuid default gen_random_uuid() primary key,
  state text unique not null,
  coi_required boolean default false not null,
  notes text
);

-- ============================================================
-- Row-level security (RLS)
-- ============================================================
alter table submissions enable row level security;
alter table redistricting_criteria enable row level security;

-- Public read access for the dashboard
create policy "Public read submissions"
  on submissions for select
  using (true);

-- Only service role can insert (voice agent uses service key)
create policy "Service insert submissions"
  on submissions for insert
  with check (true);

-- Public read for redistricting criteria
create policy "Public read redistricting_criteria"
  on redistricting_criteria for select
  using (true);

-- Service role insert/update for redistricting criteria
create policy "Service write redistricting_criteria"
  on redistricting_criteria for insert
  with check (true);

create policy "Service update redistricting_criteria"
  on redistricting_criteria for update
  using (true);

-- ============================================================
-- Indexes
-- ============================================================
create index if not exists idx_submissions_zipcode on submissions (zipcode);
create index if not exists idx_submissions_created_at on submissions (created_at desc);
create index if not exists idx_redistricting_criteria_state on redistricting_criteria (state);

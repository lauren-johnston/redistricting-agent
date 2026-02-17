import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _supabase: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!_supabase) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!url || !key) {
      throw new Error(
        "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY"
      );
    }
    _supabase = createClient(url, key);
  }
  return _supabase;
}

export type Submission = {
  id: string;
  created_at: string;
  caller_name: string | null;
  phone_number: string | null;
  consent: boolean;
  zipcode: string | null;
  address: string | null;
  community_name: string | null;
  community_description: string | null;
  key_places: string | null;
  community_boundaries: string | null;
  cultural_interests: string | null;
  economic_interests: string | null;
  community_activities: string | null;
  other_considerations: string | null;
  geographic_summary: string | null;
  primary_address: string | null;
  geocoded_landmarks: string | null;
  all_coordinates: { lat: number; lng: number; formatted_address: string }[] | null;
  geojson: GeoJSON.Feature | null;
  map_image_url: string | null;
};

"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Submission } from "@/lib/supabase";

export default function MapInner({
  submissions,
  selected,
  onSelect,
}: {
  submissions: Submission[];
  selected: Submission | null;
  onSelect: (s: Submission) => void;
}) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current).setView([39.8283, -98.5795], 4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear existing layers (except tile layer)
    map.eachLayer((layer) => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

    const bounds: L.LatLngExpression[] = [];

    submissions.forEach((s) => {
      // Draw GeoJSON polygon if available
      if (s.geojson?.geometry) {
        const isSelected = selected?.id === s.id;
        const geoLayer = L.geoJSON(s.geojson as GeoJSON.Feature, {
          style: {
            color: isSelected ? "#2563eb" : "#4285F4",
            weight: isSelected ? 3 : 2,
            fillColor: isSelected ? "#2563eb" : "#4285F4",
            fillOpacity: isSelected ? 0.3 : 0.15,
          },
        })
          .bindPopup(
            `<strong>${s.community_name || "Unnamed"}</strong><br/>${s.community_description || ""}`
          )
          .on("click", () => onSelect(s))
          .addTo(map);

        const layerBounds = geoLayer.getBounds();
        if (layerBounds.isValid()) {
          bounds.push(layerBounds.getSouthWest(), layerBounds.getNorthEast());
        }
      }
      // Otherwise place a marker at the first coordinate
      else if (s.all_coordinates && s.all_coordinates.length > 0) {
        const first = s.all_coordinates[0];
        const isSelected = selected?.id === s.id;

        const marker = L.circleMarker([first.lat, first.lng], {
          radius: isSelected ? 10 : 7,
          color: isSelected ? "#2563eb" : "#4285F4",
          fillColor: isSelected ? "#2563eb" : "#4285F4",
          fillOpacity: isSelected ? 0.8 : 0.5,
          weight: 2,
        })
          .bindPopup(
            `<strong>${s.community_name || "Unnamed"}</strong><br/>${s.community_description || ""}`
          )
          .on("click", () => onSelect(s))
          .addTo(map);

        bounds.push([first.lat, first.lng]);
      }
    });

    if (bounds.length > 0) {
      map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 14 });
    }
  }, [submissions, selected, onSelect]);

  return <div ref={containerRef} className="w-full h-full" />;
}

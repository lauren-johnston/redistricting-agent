"use client";

import { useState } from "react";
import { Submission } from "@/lib/supabase";
import { SubmissionTable } from "./SubmissionTable";
import { SubmissionDetail } from "./SubmissionDetail";
import { CommunityMap } from "./CommunityMap";
import { MapPin, List, Map } from "lucide-react";

type View = "table" | "map";

export function Dashboard({ submissions }: { submissions: Submission[] }) {
  const [view, setView] = useState<View>("table");
  const [selected, setSelected] = useState<Submission | null>(null);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* View toggle */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => setView("table")}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "table"
              ? "bg-blue-600 text-white shadow-sm"
              : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
          }`}
        >
          <List size={16} />
          Table
        </button>
        <button
          onClick={() => setView("map")}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "map"
              ? "bg-blue-600 text-white shadow-sm"
              : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
          }`}
        >
          <Map size={16} />
          Map
        </button>
      </div>

      {submissions.length === 0 ? (
        <div className="text-center py-16">
          <MapPin size={48} className="mx-auto text-gray-300 mb-4" />
          <h2 className="text-lg font-medium text-gray-900">No submissions yet</h2>
          <p className="mt-1 text-sm text-gray-500">
            Call the voice agent to submit a community of interest.
          </p>
        </div>
      ) : (
        <div className="flex gap-6">
          <div className={selected ? "w-1/2" : "w-full"}>
            {view === "table" ? (
              <SubmissionTable
                submissions={submissions}
                selected={selected}
                onSelect={setSelected}
              />
            ) : (
              <CommunityMap
                submissions={submissions}
                selected={selected}
                onSelect={setSelected}
              />
            )}
          </div>

          {selected && (
            <div className="w-1/2">
              <SubmissionDetail
                submission={selected}
                onClose={() => setSelected(null)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

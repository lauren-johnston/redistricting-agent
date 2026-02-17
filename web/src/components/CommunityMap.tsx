"use client";

import dynamic from "next/dynamic";
import { Submission } from "@/lib/supabase";

const MapInner = dynamic(() => import("./MapInner"), { ssr: false });

export function CommunityMap({
  submissions,
  selected,
  onSelect,
}: {
  submissions: Submission[];
  selected: Submission | null;
  onSelect: (s: Submission) => void;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="h-[600px]">
        <MapInner
          submissions={submissions}
          selected={selected}
          onSelect={onSelect}
        />
      </div>
    </div>
  );
}

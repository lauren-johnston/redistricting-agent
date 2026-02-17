"use client";

import { Submission } from "@/lib/supabase";
import { MapPin, User, Calendar } from "lucide-react";

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function SubmissionTable({
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
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Community
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Caller
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Location
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Date
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {submissions.map((s) => (
            <tr
              key={s.id}
              onClick={() => onSelect(s)}
              className={`cursor-pointer transition-colors hover:bg-blue-50 ${
                selected?.id === s.id ? "bg-blue-50 ring-1 ring-inset ring-blue-200" : ""
              }`}
            >
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  <MapPin size={14} className="text-blue-500 shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {s.community_name || "Unnamed"}
                    </div>
                    <div className="text-xs text-gray-500 line-clamp-1">
                      {s.community_description || "—"}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  <User size={14} className="text-gray-400 shrink-0" />
                  <span className="text-sm text-gray-700">
                    {s.caller_name || "Anonymous"}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4">
                <span className="text-sm text-gray-600">
                  {s.zipcode || "—"}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  <Calendar size={14} className="text-gray-400 shrink-0" />
                  <span className="text-sm text-gray-500">
                    {formatDate(s.created_at)}
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

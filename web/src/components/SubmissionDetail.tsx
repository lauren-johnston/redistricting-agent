"use client";

import { Submission } from "@/lib/supabase";
import { X, MapPin, Users, Landmark, DollarSign, Heart, FileText } from "lucide-react";

function Section({
  icon: Icon,
  title,
  content,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  content: string | null | undefined;
}) {
  if (!content) return null;
  return (
    <div className="py-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className="text-gray-400" />
        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          {title}
        </h4>
      </div>
      <p className="text-sm text-gray-800 leading-relaxed">{content}</p>
    </div>
  );
}

export function SubmissionDetail({
  submission: s,
  onClose,
}: {
  submission: Submission;
  onClose: () => void;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden sticky top-8">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {s.community_name || "Unnamed Community"}
          </h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {s.caller_name || "Anonymous"} · {s.zipcode || "No zip"}
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={18} />
        </button>
      </div>

      {/* Map image */}
      {s.map_image_url && (
        <div className="border-b border-gray-100">
          <img
            src={s.map_image_url}
            alt={`Map of ${s.community_name}`}
            className="w-full h-48 object-cover"
          />
        </div>
      )}

      {/* Details */}
      <div className="px-6 py-2 divide-y divide-gray-100 max-h-[60vh] overflow-y-auto">
        <Section icon={FileText} title="Description" content={s.community_description} />
        <Section icon={MapPin} title="Key Places" content={s.key_places} />
        <Section icon={Landmark} title="Boundaries" content={s.community_boundaries} />
        <Section icon={MapPin} title="Geographic Summary" content={s.geographic_summary} />
        <Section icon={Users} title="Cultural Interests" content={s.cultural_interests} />
        <Section icon={DollarSign} title="Economic Interests" content={s.economic_interests} />
        <Section icon={Heart} title="Community Activities" content={s.community_activities} />
        <Section icon={FileText} title="Other Considerations" content={s.other_considerations} />

        {s.geocoded_landmarks && (
          <div className="py-3">
            <div className="flex items-center gap-2 mb-1">
              <MapPin size={14} className="text-gray-400" />
              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Geocoded Landmarks
              </h4>
            </div>
            <p className="text-sm text-gray-600">{s.geocoded_landmarks}</p>
          </div>
        )}
      </div>
    </div>
  );
}

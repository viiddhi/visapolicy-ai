"use client";
import { useState } from "react";
import type { FeedItem } from "@/lib/api";
import ImpactBadge from "./ImpactBadge";

export default function ChangeCard({ item }: { item: FeedItem }) {
  const [expanded, setExpanded] = useState(false);
  const { change, relevance_reasons, relevance_score } = item;

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {/* Top bar */}
      <div className={`h-1 ${change.impact_level === "high" ? "bg-red-500" : change.impact_level === "medium" ? "bg-amber-400" : "bg-green-400"}`} />

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-gray-400 mb-1 truncate">{change.document_title}</p>
            <h3 className="font-semibold text-gray-900 leading-snug">{change.topic}</h3>
          </div>
          <ImpactBadge level={change.impact_level} />
        </div>

        {/* Summary */}
        <p className="text-sm text-gray-600 leading-relaxed mb-4">{change.plain_english_summary}</p>

        {/* Why it's relevant */}
        {relevance_reasons.length > 0 && (
          <div className="bg-blue-50 rounded-lg px-3 py-2 mb-4">
            <p className="text-xs font-semibold text-blue-700 mb-1">Why this matters to you</p>
            <ul className="space-y-0.5">
              {relevance_reasons.map((r, i) => (
                <li key={i} className="text-xs text-blue-600 flex items-start gap-1.5">
                  <span className="mt-0.5 shrink-0">›</span>{r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action required banner */}
        {change.action_required && change.action_description && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 flex gap-2">
            <span className="text-amber-500 shrink-0 mt-0.5">⚠</span>
            <div>
              <p className="text-xs font-semibold text-amber-800 mb-0.5">Action required</p>
              <p className="text-xs text-amber-700">{change.action_description}</p>
            </div>
          </div>
        )}

        {/* Before / After diff toggle */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-brand-light font-medium hover:underline"
        >
          {expanded ? "Hide rule comparison ↑" : "See before / after rule text ↓"}
        </button>

        {expanded && (
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div className="bg-red-50 rounded-lg p-3">
              <p className="font-semibold text-red-700 mb-1">BEFORE</p>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{change.old_rule}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="font-semibold text-green-700 mb-1">AFTER</p>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{change.new_rule}</p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
          <div className="flex gap-2 flex-wrap">
            {(change.visa_categories_affected || []).map((v) => (
              <span key={v} className="text-xs bg-blue-50 text-blue-700 rounded-full px-2 py-0.5">{v}</span>
            ))}
          </div>
          <div className="flex items-center gap-3">
            {change.effective_at && (
              <span className="text-xs text-gray-400">Effective {change.effective_at}</span>
            )}
            {change.document_source_url && (
              <a
                href={change.document_source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-brand-light hover:underline"
              >
                Source ↗
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

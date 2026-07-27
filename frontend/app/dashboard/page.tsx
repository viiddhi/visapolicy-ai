"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getDashboard, getMe, type DashboardResponse, type Profile } from "@/lib/api";
import { clearToken, isLoggedIn } from "@/lib/auth";
import ChangeCard from "@/components/ChangeCard";
import ImpactBadge from "@/components/ImpactBadge";

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [filter, setFilter] = useState<"all" | "high" | "action">("all");
  const [loading, setLoading] = useState(true);
  const [liveAlert, setLiveAlert] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) { router.replace("/"); return; }

    Promise.all([getMe(), getDashboard()])
      .then(([p, d]) => { setProfile(p); setData(d); })
      .catch(() => { clearToken(); router.replace("/"); })
      .finally(() => setLoading(false));

    // Real-time SSE connection
    const token = localStorage.getItem("vp_token");
    if (token) {
      const es = new EventSource(`/api/v1/stream/alerts?token=${token}`);
      es.addEventListener("alert", (e) => {
        const ev = JSON.parse(e.data);
        setLiveAlert(ev.topic ?? "New rule change detected");
        getDashboard().then(setData);
        setTimeout(() => setLiveAlert(null), 6000);
      });
      esRef.current = es;
    }
    return () => esRef.current?.close();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-sm animate-pulse">Loading your dashboard…</div>
      </div>
    );
  }

  const feed = data?.feed ?? [];
  const stats = data?.stats;

  const filtered = feed.filter((item) => {
    if (filter === "high") return item.change.impact_level === "high";
    if (filter === "action") return item.change.action_required;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="bg-brand border-b border-brand/80 px-6 py-3 flex items-center justify-between">
        <h1 className="text-white font-bold text-lg">
          Visapolicy<span className="text-blue-300">.ai</span>
        </h1>
        <div className="flex items-center gap-4">
          <span className="text-blue-200 text-sm">{profile?.name ?? profile?.email}</span>
          <button
            onClick={() => { clearToken(); router.push("/"); }}
            className="text-blue-300 hover:text-white text-sm transition"
          >
            Sign out
          </button>
        </div>
      </nav>

      {/* Live alert toast */}
      {liveAlert && (
        <div className="fixed top-4 right-4 z-50 bg-red-600 text-white px-4 py-3 rounded-xl shadow-lg text-sm max-w-sm animate-bounce">
          <p className="font-semibold">🔴 New rule change detected</p>
          <p className="opacity-90 mt-0.5">{liveAlert}</p>
        </div>
      )}

      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Profile summary pill */}
        {profile?.primary_visa_type && (
          <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 mb-6 flex items-center gap-3">
            <div className="bg-brand text-white text-xs font-bold px-2.5 py-1 rounded-lg">
              {profile.primary_visa_type}
            </div>
            <div className="text-sm text-gray-600 flex gap-3 flex-wrap">
              {profile.employer_type && <span>{profile.employer_type.replace("_", " ")}</span>}
              {profile.country_of_birth && <span>🌍 {profile.country_of_birth}</span>}
              {profile.gc_stage && profile.gc_stage !== "none" && (
                <span className="text-blue-600">GC: {profile.gc_stage.replace(/_/g, " ")}</span>
              )}
            </div>
            <button
              onClick={() => router.push("/profile")}
              className="ml-auto text-xs text-gray-400 hover:text-gray-600"
            >
              Edit profile
            </button>
          </div>
        )}

        {/* Stats row */}
        {stats && (
          <div className="grid grid-cols-3 gap-3 mb-6">
            {[
              { label: "Relevant changes", value: stats.total_relevant, color: "text-gray-900" },
              { label: "High impact", value: stats.high_impact, color: "text-red-600" },
              { label: "Action required", value: stats.action_required, color: "text-amber-600" },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
                <p className="text-xs text-gray-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filter tabs */}
        <div className="flex gap-2 mb-5">
          {[
            { key: "all", label: "All relevant" },
            { key: "high", label: "High impact" },
            { key: "action", label: "Action required" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key as typeof filter)}
              className={`px-3 py-1.5 text-sm rounded-lg font-medium transition ${
                filter === tab.key
                  ? "bg-brand text-white"
                  : "bg-white border border-gray-200 text-gray-600 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Feed */}
        {filtered.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-3">✓</p>
            <p className="font-medium">No changes matching this filter</p>
            <p className="text-sm mt-1">We'll alert you the moment something relevant is published</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filtered.map((item) => (
              <ChangeCard key={item.change.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getProfile, updateProfile, type Profile } from "@/lib/api";
import { clearToken, isLoggedIn } from "@/lib/auth";
import {
  VisaStatusFields,
  GreenCardFields,
  EmploymentFields,
  DependentsFields,
  AlertPreferenceFields,
} from "@/components/ProfileFields";

const SECTIONS = [
  { title: "Visa status", subtitle: "Your current immigration status", Fields: VisaStatusFields },
  { title: "Green card journey", subtitle: "Are you pursuing permanent residence?", Fields: GreenCardFields },
  { title: "Employment", subtitle: "Your work situation affects which rules apply to you", Fields: EmploymentFields },
  { title: "Dependents & OPT", subtitle: "We'll alert you about changes affecting your dependents too", Fields: DependentsFields },
  { title: "Alert preferences", subtitle: "How would you like to receive alerts?", Fields: AlertPreferenceFields },
];

export default function ProfilePage() {
  const router = useRouter();
  const [original, setOriginal] = useState<Partial<Profile> | null>(null);
  const [data, setData] = useState<Partial<Profile>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) { router.replace("/"); return; }

    getProfile()
      .then((p) => { setOriginal(p); setData(p); })
      .catch(() => { clearToken(); router.replace("/"); })
      .finally(() => setLoading(false));
  }, [router]);

  const update = (updates: Partial<Profile>) => {
    setSaved(false);
    setData((d) => ({ ...d, ...updates }));
  };

  const dirty = original ? JSON.stringify(original) !== JSON.stringify(data) : false;

  async function save() {
    setSaving(true);
    setError("");
    try {
      const updated = await updateProfile(data);
      setOriginal(updated);
      setData(updated);
      setSaved(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save changes");
    } finally {
      setSaving(false);
    }
  }

  function discard() {
    if (original) setData(original);
    setSaved(false);
    setError("");
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-sm animate-pulse">Loading your profile…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => router.push("/dashboard")}
              className="text-sm text-gray-400 hover:text-gray-600 mb-2"
            >
              ← Back to dashboard
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Edit profile</h1>
            <p className="text-sm text-gray-500 mt-1">
              Update any section below — everything else stays as-is.
            </p>
          </div>
        </div>

        {/* Sections */}
        <div className="space-y-6">
          {SECTIONS.map(({ title, subtitle, Fields }) => (
            <div key={title} className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
              <p className="text-sm text-gray-500 mt-0.5 mb-5">{subtitle}</p>
              <Fields data={data} onChange={update} />
            </div>
          ))}
        </div>

        {/* Save bar */}
        <div className="sticky bottom-4 mt-6">
          <div className="bg-white border border-gray-200 rounded-xl shadow-lg px-5 py-4 flex items-center justify-between">
            <div className="text-sm">
              {error && <span className="text-red-600">{error}</span>}
              {!error && saved && <span className="text-green-600">✓ Changes saved</span>}
              {!error && !saved && dirty && <span className="text-amber-600">You have unsaved changes</span>}
              {!error && !saved && !dirty && <span className="text-gray-400">No changes yet</span>}
            </div>
            <div className="flex gap-2">
              <button
                onClick={discard}
                disabled={!dirty || saving}
                className="text-sm text-gray-500 hover:text-gray-700 disabled:opacity-30 px-3 py-2"
              >
                Discard
              </button>
              <button
                onClick={save}
                disabled={!dirty || saving}
                className="bg-brand text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-opacity-90 disabled:opacity-40"
              >
                {saving ? "Saving…" : "Save changes"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

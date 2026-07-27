"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getProfile, type Profile } from "@/lib/api";
import { clearToken, isLoggedIn } from "@/lib/auth";
import OnboardingWizard from "@/components/OnboardingWizard";

export default function OnboardingPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) { router.replace("/"); return; }

    getProfile()
      .then(setProfile)
      .catch(() => { clearToken(); router.replace("/"); })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-sm animate-pulse">Loading your profile…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-brand">
          Visapolicy<span className="text-brand-light">.ai</span>
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {profile?.onboarding_completed ? "Update your immigration profile" : "Let's build your immigration profile"}
        </p>
      </div>
      <OnboardingWizard initialData={profile ?? undefined} onComplete={() => router.push("/dashboard")} />
    </div>
  );
}

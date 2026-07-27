"use client";
import { useState } from "react";
import { updateProfile, type Profile } from "@/lib/api";
import {
  VisaStatusFields,
  GreenCardFields,
  EmploymentFields,
  DependentsFields,
  AlertPreferenceFields,
} from "./ProfileFields";

const STEPS = [
  { title: "Visa status", subtitle: "Tell us about your current immigration status" },
  { title: "Green card journey", subtitle: "Are you pursuing permanent residence?" },
  { title: "Employment", subtitle: "Your work situation affects which rules apply to you" },
  { title: "Dependents & OPT", subtitle: "We'll alert you about changes affecting your dependents too" },
  { title: "Alert preferences", subtitle: "How would you like to receive alerts?" },
];

export default function OnboardingWizard({
  onComplete,
  initialData,
}: {
  onComplete: () => void;
  initialData?: Partial<Profile>;
}) {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<Partial<Profile>>({
    alert_frequency: "daily",
    min_impact_level: "medium",
    ...initialData,
  });
  const [saving, setSaving] = useState(false);

  const update = (updates: Partial<Profile>) => setData((d) => ({ ...d, ...updates }));

  const next = async () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      setSaving(true);
      try {
        await updateProfile({ ...data, onboarding_completed: true });
        onComplete();
      } finally {
        setSaving(false);
      }
    }
  };

  const stepComponents = [
    <VisaStatusFields key={0} data={data} onChange={update} />,
    <GreenCardFields key={1} data={data} onChange={update} />,
    <EmploymentFields key={2} data={data} onChange={update} />,
    <DependentsFields key={3} data={data} onChange={update} />,
    <AlertPreferenceFields key={4} data={data} onChange={update} />,
  ];

  return (
    <div className="max-w-lg mx-auto">
      {/* Progress */}
      <div className="flex gap-1.5 mb-8">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-all ${i <= step ? "bg-brand" : "bg-gray-200"}`}
          />
        ))}
      </div>

      {/* Step header */}
      <div className="mb-6">
        <p className="text-xs font-medium text-brand-light uppercase tracking-wide mb-1">
          Step {step + 1} of {STEPS.length}
        </p>
        <h2 className="text-2xl font-bold text-gray-900">{STEPS[step].title}</h2>
        <p className="text-sm text-gray-500 mt-1">{STEPS[step].subtitle}</p>
      </div>

      {/* Step content */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
        {stepComponents[step]}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          className="text-sm text-gray-500 hover:text-gray-700 disabled:opacity-30"
        >
          ← Back
        </button>
        <button
          onClick={next}
          disabled={saving}
          className="bg-brand text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-opacity-90 disabled:opacity-60"
        >
          {saving ? "Saving…" : step === STEPS.length - 1 ? "Go to dashboard →" : "Continue →"}
        </button>
      </div>
    </div>
  );
}

"use client";
import type { Profile } from "@/lib/api";

export const VISA_TYPES = ["H-1B", "F-1", "O-1", "L-1", "TN", "J-1", "EB-1", "EB-2", "EB-3", "Other"];
export const GC_STAGES = [
  { value: "none", label: "Not pursuing green card" },
  { value: "perm_filed", label: "PERM / Labor Certification filed" },
  { value: "i140_filed", label: "I-140 filed" },
  { value: "i140_approved", label: "I-140 approved, waiting for priority date" },
  { value: "i485_filed", label: "I-485 (Adjustment of Status) filed" },
  { value: "gc_approved", label: "Green card approved" },
];
export const EMPLOYER_TYPES = [
  { value: "big_tech", label: "Large tech company (1000+ employees)" },
  { value: "small_company", label: "Small/mid company" },
  { value: "nonprofit", label: "Nonprofit / University" },
  { value: "consulting", label: "IT consulting firm" },
  { value: "staffing", label: "Staffing / body shop" },
  { value: "self_employed", label: "Self-employed / entrepreneur" },
];
export const PLACEMENT_TYPES = [
  { value: "direct", label: "I work directly at my employer's office" },
  { value: "third_party", label: "I'm placed at a client/vendor site" },
  { value: "bench", label: "Currently on bench (between projects)" },
];

export type FieldProps = {
  data: Partial<Profile>;
  onChange: (updates: Partial<Profile>) => void;
};

export function VisaStatusFields({ data, onChange }: FieldProps) {
  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Primary visa type *</label>
        <div className="grid grid-cols-3 gap-2">
          {VISA_TYPES.map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ primary_visa_type: v })}
              className={`py-2 px-3 text-sm rounded-lg border transition ${
                data.primary_visa_type === v
                  ? "border-brand bg-brand text-white"
                  : "border-gray-200 hover:border-brand-light"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Visa status</label>
        <select
          value={data.visa_status ?? ""}
          onChange={(e) => onChange({ visa_status: e.target.value })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Select status</option>
          <option value="active">Active / Approved</option>
          <option value="pending">Pending approval</option>
          <option value="expired">Expired / Grace period</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">I-94 / Status expiry date</label>
        <input
          type="date"
          value={data.authorized_until ?? ""}
          onChange={(e) => onChange({ authorized_until: e.target.value })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
        />
      </div>
    </div>
  );
}

export function GreenCardFields({ data, onChange }: FieldProps) {
  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Green card stage</label>
        <div className="space-y-2">
          {GC_STAGES.map((s) => (
            <button
              key={s.value}
              type="button"
              onClick={() => onChange({ gc_stage: s.value })}
              className={`w-full text-left py-2.5 px-3 text-sm rounded-lg border transition ${
                data.gc_stage === s.value
                  ? "border-brand bg-brand-soft text-brand"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Priority date</label>
          <input
            type="date"
            value={data.priority_date ?? ""}
            onChange={(e) => onChange({ priority_date: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Country of birth</label>
          <input
            type="text"
            placeholder="e.g. India"
            value={data.country_of_birth ?? ""}
            onChange={(e) => onChange({ country_of_birth: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
          <p className="text-xs text-gray-400 mt-1">Matters for EB priority date backlog</p>
        </div>
      </div>
    </div>
  );
}

export function EmploymentFields({ data, onChange }: FieldProps) {
  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Employer type</label>
        <div className="space-y-2">
          {EMPLOYER_TYPES.map((e) => (
            <button
              key={e.value}
              type="button"
              onClick={() => onChange({ employer_type: e.value })}
              className={`w-full text-left py-2.5 px-3 text-sm rounded-lg border transition ${
                data.employer_type === e.value
                  ? "border-brand bg-brand-soft text-brand"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              {e.label}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Work placement</label>
        <div className="space-y-2">
          {PLACEMENT_TYPES.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => onChange({ placement_type: p.value })}
              className={`w-full text-left py-2.5 px-3 text-sm rounded-lg border transition ${
                data.placement_type === p.value
                  ? "border-brand bg-brand-soft text-brand"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Degree field</label>
        <input
          type="text"
          placeholder="e.g. Computer Science, Electrical Engineering"
          value={data.degree_field ?? ""}
          onChange={(e) => onChange({ degree_field: e.target.value })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
        />
      </div>
    </div>
  );
}

export function DependentsFields({ data, onChange }: FieldProps) {
  const deps = data.dependent_visa_types ?? [];
  const toggle = (v: string) =>
    onChange({ dependent_visa_types: deps.includes(v) ? deps.filter((d) => d !== v) : [...deps, v] });

  return (
    <div className="space-y-5">
      {data.primary_visa_type === "F-1" && (
        <div className="bg-blue-50 rounded-lg p-4 space-y-3">
          <p className="text-sm font-medium text-blue-800">F-1 / OPT details</p>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={data.on_opt ?? false}
              onChange={(e) => onChange({ on_opt: e.target.checked })}
              className="rounded"
            />
            I am currently on OPT
          </label>
          {data.on_opt && (
            <div className="grid grid-cols-2 gap-3 mt-2">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">OPT type</label>
                <select
                  value={data.opt_type ?? ""}
                  onChange={(e) => onChange({ opt_type: e.target.value })}
                  className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
                >
                  <option value="">Select</option>
                  <option value="regular">Regular OPT (12 months)</option>
                  <option value="stem">STEM OPT extension (24 months)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">OPT expiry</label>
                <input
                  type="date"
                  value={data.opt_expiry ?? ""}
                  onChange={(e) => onChange({ opt_expiry: e.target.value })}
                  className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
                />
              </div>
            </div>
          )}
        </div>
      )}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Dependents (check all that apply)</label>
        <div className="space-y-2">
          {["H-4", "H-4 EAD", "F-2", "L-2", "O-3"].map((d) => (
            <label key={d} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={deps.includes(d)}
                onChange={() => toggle(d)}
                className="rounded"
              />
              {d}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

export function AlertPreferenceFields({ data, onChange }: FieldProps) {
  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Alert frequency</label>
        {[
          { value: "realtime", label: "Real-time", sub: "Notified the moment a rule changes" },
          { value: "daily", label: "Daily digest", sub: "One email per day with all changes" },
          { value: "weekly", label: "Weekly digest", sub: "Weekly summary every Monday" },
        ].map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange({ alert_frequency: opt.value })}
            className={`w-full text-left py-3 px-4 rounded-lg border mb-2 transition ${
              data.alert_frequency === opt.value
                ? "border-brand bg-brand-soft"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <p className={`text-sm font-medium ${data.alert_frequency === opt.value ? "text-brand" : ""}`}>
              {opt.label}
            </p>
            <p className="text-xs text-gray-400">{opt.sub}</p>
          </button>
        ))}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Minimum impact level to alert</label>
        <div className="grid grid-cols-3 gap-2">
          {[
            { value: "low", label: "All changes", color: "text-green-700 border-green-200 bg-green-50" },
            { value: "medium", label: "Medium+", color: "text-amber-700 border-amber-200 bg-amber-50" },
            { value: "high", label: "High only", color: "text-red-700 border-red-200 bg-red-50" },
          ].map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange({ min_impact_level: opt.value })}
              className={`py-2 px-3 text-sm font-medium rounded-lg border transition ${
                data.min_impact_level === opt.value ? opt.color + " ring-2 ring-offset-1 ring-current" : "border-gray-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

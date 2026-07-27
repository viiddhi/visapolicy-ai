const styles = {
  high:   "bg-red-100 text-red-700 ring-red-200",
  medium: "bg-amber-100 text-amber-700 ring-amber-200",
  low:    "bg-green-100 text-green-700 ring-green-200",
};

const labels = { high: "High impact", medium: "Medium impact", low: "Low impact" };

export default function ImpactBadge({ level }: { level: "low" | "medium" | "high" }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ring-1 ${styles[level]}`}>
      {level === "high" && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
      {labels[level]}
    </span>
  );
}

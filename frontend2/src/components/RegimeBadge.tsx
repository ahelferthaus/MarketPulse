import { REGIME_DEFINITIONS } from "../lib/mockData";

interface RegimeBadgeProps {
  regime: string;
  label: string;
}

export default function RegimeBadge({ label }: RegimeBadgeProps) {
  const regimeDef = REGIME_DEFINITIONS.find(
    (r) => r.label.toLowerCase() === label.toLowerCase()
  );
  const color = regimeDef?.color ?? "#6B7280";

  return (
    <span
      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold text-white"
      style={{ backgroundColor: color }}
    >
      {label}
    </span>
  );
}

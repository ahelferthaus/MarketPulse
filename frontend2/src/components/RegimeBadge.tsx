import { zoneFor, zoneById } from "../lib/theme";

interface RegimeBadgeProps {
  /** Either a 0-100 score or a regime id / label. */
  score?: number;
  regime?: string;
  label?: string;
}

/** Zone chip: tinted ground, colored text + border — contrast-safe on white. */
export default function RegimeBadge({ score, regime, label }: RegimeBadgeProps) {
  const zone =
    score != null
      ? zoneFor(score)
      : zoneById(regime ?? "") ??
        zoneFor(50);
  const text = label ?? zone.label;
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide"
      style={{
        color: zone.text,
        backgroundColor: `${zone.onPaper}14`,
        border: `1px solid ${zone.onPaper}55`,
      }}
    >
      {text}
    </span>
  );
}

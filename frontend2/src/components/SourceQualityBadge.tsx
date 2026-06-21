interface SourceQualityBadgeProps {
  confidence: number;
}

export default function SourceQualityBadge({ confidence }: SourceQualityBadgeProps) {
  const color =
    confidence >= 90
      ? "#22C55E"
      : confidence >= 70
        ? "#3B82F6"
        : confidence >= 50
          ? "#EAB308"
          : confidence >= 30
            ? "#F97316"
            : "#DC2626";

  const label =
    confidence >= 90
      ? "High"
      : confidence >= 70
        ? "Good"
        : confidence >= 50
          ? "Fair"
          : confidence >= 30
            ? "Low"
            : "Poor";

  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
      style={{ backgroundColor: color + "20", color }}
    >
      {label} ({confidence}%)
    </span>
  );
}

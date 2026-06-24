import {
  MOCK_COMPOSITE_SCORE,
  MOCK_SUB_INDICES,
  MOCK_EXPLANATION,
  MOCK_REGIME_LABEL,
  REGIME_DEFINITIONS,
} from "../lib/mockData";
import RegimeBadge from "./RegimeBadge";

interface EmbedWidgetProps {
  size: "small" | "medium" | "full";
  theme: "light" | "dark";
}

export default function EmbedWidget({ size, theme }: EmbedWidgetProps) {
  const isDark = theme === "dark";
  const bg = isDark ? "#0F172A" : "#FFFFFF";
  const text = isDark ? "#F8FAFC" : "#0F172A";
  const sub = isDark ? "#94A3B8" : "#64748B";
  const border = isDark ? "#1E293B" : "#E2E8F0";

  const wrapperClasses =
    size === "small"
      ? "max-w-xs"
      : size === "medium"
        ? "max-w-md"
        : "max-w-lg";

  return (
    <div
      className={`${wrapperClasses} rounded-xl border overflow-hidden`}
      style={{ backgroundColor: bg, borderColor: border }}
    >
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: border }}>
        <div className="flex items-center justify-between">
          <div>
            <div
              className="text-xs font-bold tracking-widest uppercase mb-1"
              style={{ color: "#D4AF37" }}
            >
              WESTWOOD
            </div>
            <div className="text-xs" style={{ color: sub }}>
              MarketPulse
            </div>
          </div>
          <RegimeBadge regime={MOCK_REGIME_LABEL} label={MOCK_REGIME_LABEL} />
        </div>

        {/* Score */}
        <div className="flex items-baseline gap-3 mt-3">
          <span className="text-5xl font-extrabold" style={{ color: text }}>
            {MOCK_COMPOSITE_SCORE}
          </span>
        </div>
      </div>

      {/* Sub-indices */}
      <div className="p-4 space-y-3">
        {Object.entries(MOCK_SUB_INDICES).map(([key, data]) => {
          const rDef = REGIME_DEFINITIONS.find(
            (r) => r.label === data.label
          );
          const c = rDef?.color ?? "#22C55E";
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span
                  className="text-xs font-medium capitalize"
                  style={{ color: sub }}
                >
                  {key}
                </span>
                <span className="text-xs font-semibold" style={{ color: text }}>
                  {data.score}
                </span>
              </div>
              <div
                className="w-full h-2 rounded-full overflow-hidden"
                style={{ backgroundColor: isDark ? "#1E293B" : "#F1F5F9" }}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${data.score}%`, backgroundColor: c }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Explanation */}
      <div className="px-4 pb-2">
        <p className="text-xs leading-relaxed line-clamp-2" style={{ color: sub }}>
          {MOCK_EXPLANATION}
        </p>
      </div>

      {/* Footer */}
      <div
        className="px-4 py-3 border-t text-center"
        style={{ borderColor: border }}
      >
        <span className="text-xs" style={{ color: sub }}>
          Powered by{" "}
          <span className="font-semibold" style={{ color: "#D4AF37" }}>
            Westwood MarketPulse
          </span>
        </span>
      </div>
    </div>
  );
}

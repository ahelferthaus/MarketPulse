import type { ReactNode } from "react";
import { BRAND } from "../lib/theme";

interface ExplanationBoxProps {
  icon: ReactNode;
  title: string;
  text: string;
  timestamp?: string;
}

export default function ExplanationBox({
  icon,
  title,
  text,
  timestamp,
}: ExplanationBoxProps) {
  return (
    <div className="mp-panel p-5 fade-in" style={{ borderLeft: `3px solid ${BRAND.gold}` }}>
      <div className="flex items-center gap-2 mb-2">
        <span style={{ color: BRAND.goldDeep }}>{icon}</span>
        <h3 className="font-display text-[15px]" style={{ color: BRAND.ink }}>{title}</h3>
      </div>
      <p className="text-[13px] leading-relaxed" style={{ color: BRAND.slate }}>{text}</p>
      {timestamp && (
        <p className="font-data text-[11px] mt-3" style={{ color: BRAND.slateFaint }}>{timestamp}</p>
      )}
    </div>
  );
}

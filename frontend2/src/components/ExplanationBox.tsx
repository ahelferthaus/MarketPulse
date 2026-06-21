import type { ReactNode } from "react";

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
    <div
      className="rounded-xl p-5 fade-in"
      style={{ backgroundColor: "#F1F5F9" }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-slate-600">{icon}</span>
        <h3 className="font-bold text-slate-800 text-sm">{title}</h3>
      </div>
      <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
      {timestamp && (
        <p className="text-xs text-slate-400 mt-3">{timestamp}</p>
      )}
    </div>
  );
}

/**
 * MarketPulse design tokens — single source of truth for chart + zone color.
 *
 * Palettes are validated (dataviz six-checks) against both the navy hero
 * surface and the white card surface:
 *   zones on navy:  #C24A3E #C4791F #8B93A1 #6F9A3D #2E8F5B   (PASS)
 *   zones on white: #B3382E #C4791F #8B93A1 #6F9A3D #1F7A4D   (PASS)
 *   sub-indices:    #3B82D6 #6E3F87 #0E8A74                   (PASS, protan ΔE 25)
 * MP-3 is the deliberately low-chroma neutral midpoint of a diverging scale.
 */

export const BRAND = {
  navy950: "#081A33",
  navy900: "#0B2240",
  navy800: "#14355C",
  ink: "#16233A",
  paper: "#F5F6F8",
  card: "#FFFFFF",
  hairline: "#E2E6EC",
  gold: "#C8A951",
  goldDeep: "#A8842F",
  slate: "#5C6B80",
  slateFaint: "#8B96A5",
};

export interface Zone {
  id: string;
  zone: string;      // "MP-1"
  label: string;     // "Panic"
  short: string;     // one-word read
  min: number;
  max: number;       // inclusive upper bound
  onNavy: string;    // arc / dark-surface color
  onPaper: string;   // chart-band / light-surface color
  text: string;      // chip text color on white (contrast-safe)
}

/** Empirically-derived asymmetric bands — keep in sync with backend SPEC. */
export const ZONES: Zone[] = [
  { id: "mp1_capitulation", zone: "MP-1", label: "Panic", short: "Extreme risk-off",
    min: 0,  max: 24,  onNavy: "#C24A3E", onPaper: "#B3382E", text: "#A33328" },
  { id: "mp2_defensive",    zone: "MP-2", label: "Defensive",    short: "Risk-off",
    min: 24, max: 44,  onNavy: "#C4791F", onPaper: "#C4791F", text: "#8F5A14" },
  { id: "mp3_neutral",      zone: "MP-3", label: "Neutral",      short: "Balanced",
    min: 44, max: 55,  onNavy: "#8B93A1", onPaper: "#8B93A1", text: "#5C6B80" },
  { id: "mp4_risk_on",      zone: "MP-4", label: "Risk-On",      short: "Risk-on",
    min: 55, max: 75,  onNavy: "#6F9A3D", onPaper: "#6F9A3D", text: "#4E7325" },
  { id: "mp5_euphoria",     zone: "MP-5", label: "Euphoria",     short: "Extreme risk-on",
    min: 75, max: 100, onNavy: "#2E8F5B", onPaper: "#1F7A4D", text: "#186241" },
];

export function zoneFor(score: number): Zone {
  return ZONES.find((z) => score <= z.max) ?? ZONES[2];
}

export function zoneById(id: string): Zone {
  return ZONES.find((z) => z.id === id) ?? ZONES[2];
}

/** Sub-index series colors — categorical, fixed order, never cycled. */
export const SERIES = {
  classic: "#3B82D6",
  narrative: "#6E3F87",
  positioning: "#0E8A74",
} as const;

export const SERIES_LABELS: Record<keyof typeof SERIES, string> = {
  classic: "Classic",
  narrative: "Narrative",
  positioning: "Positioning",
};

/** Editorial headline derived from regime + direction — the page's voice. */
export function headline(regimeId: string, direction: string): string {
  const d = direction === "rising" ? "rising" : direction === "falling" ? "falling" : "stable";
  const map: Record<string, Record<string, string>> = {
    mp1_capitulation: {
      rising: "Panic, with a pulse returning.",
      stable: "Panic. The exits are crowded.",
      falling: "Panic, and still deteriorating.",
    },
    mp2_defensive: {
      rising: "Defensive, but thawing.",
      stable: "Defensive. Caution is the position.",
      falling: "Defensive, and getting more so.",
    },
    mp3_neutral: {
      rising: "Neutral, leaning warmer.",
      stable: "Neutral. The market is undecided.",
      falling: "Neutral, leaning colder.",
    },
    mp4_risk_on: {
      rising: "Risk appetite is building.",
      stable: "Risk-on, and steady.",
      falling: "Risk-on, but cooling.",
    },
    mp5_euphoria: {
      rising: "Euphoria — extremes cut both ways.",
      stable: "Euphoria. Handle with care.",
      falling: "Euphoria, starting to deflate.",
    },
  };
  return map[regimeId]?.[d] ?? "The market, measured.";
}

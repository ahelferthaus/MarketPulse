"""Static export generator for Westwood MarketPulse.

Generates sanitized JSON payloads for public consumption. Exports contain
ONLY derived scores — no raw prices, no ticker data, no proprietary information.

See SPEC.md section 8 for the exact export format specification.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.domain.score import Regime

logger = logging.getLogger(__name__)


class ExportManager:
    """Manages generation and persistence of static JSON exports.

    Exports are sanitized payloads suitable for public websites and
    embeddable widgets. They contain only derived scores and regime
    classifications — never raw prices or ticker symbols.
    """

    def __init__(self, payloads_dir: Optional[str] = None) -> None:
        self.payloads_dir: Path = Path(
            payloads_dir or settings.static_payloads_dir
        )
        self.payloads_dir.mkdir(parents=True, exist_ok=True)

    # ── Export generation ─────────────────────────────────────────────────

    def generate_static_export(
        self,
        market_id: str,
        timestamp: Optional[datetime] = None,
        composite_score: float = 50.0,
        regime: str = "mp3_neutral",
        direction: str = "stable",
        classic_score: float = 50.0,
        classic_change_1d: int = 0,
        classic_change_1w: int = 0,
        narrative_score: float = 50.0,
        narrative_change_1d: int = 0,
        narrative_change_1w: int = 0,
        positioning_score: float = 50.0,
        positioning_change_1d: int = 0,
        positioning_change_1w: int = 0,
        confidence: float = 50.0,
        explanation: str = "",
        components: Optional[List[Dict[str, Any]]] = None,
        data_quality: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a sanitized static export payload.

        All parameters are optional with sensible defaults for graceful
        degradation when data is missing. The resulting payload follows
        the SPEC.md section 8 format exactly.

        Args:
            market_id: Market identifier (e.g., 'sp500').
            timestamp: Score timestamp. Defaults to now.
            composite_score: Composite headline score (0-100).
            regime: Regime code (e.g., 'mp4_risk_on').
            direction: Direction: 'rising', 'falling', or 'stable'.
            classic_score: Classic index score (0-100).
            classic_change_1d: 1-day change in classic score.
            classic_change_1w: 1-week change in classic score.
            narrative_score: Narrative index score (0-100).
            narrative_change_1d: 1-day change in narrative score.
            narrative_change_1w: 1-week change in narrative score.
            positioning_score: Positioning index score (0-100).
            positioning_change_1d: 1-day change in positioning score.
            positioning_change_1w: 1-week change in positioning score.
            confidence: Overall confidence (0-100).
            explanation: Plain-English explanation sentence.
            components: Optional list of component breakdown dicts.
            data_quality: Optional data quality report dict.

        Returns:
            Sanitized export dict ready for JSON serialization.
        """
        ts = timestamp or datetime.now(timezone.utc)
        regime_enum = Regime(regime) if regime else Regime.MP3_NEUTRAL
        regime_label = regime_enum.label

        payload: Dict[str, Any] = {
            "generated_at": ts.isoformat().replace("+00:00", "Z"),
            "marketpulse": {
                "market": market_id,
                "timestamp": ts.isoformat().replace("+00:00", "Z"),
                "composite": {
                    "score": round(composite_score),
                    "regime": regime_enum.value,
                    "label": regime_label,
                    "direction": direction,
                },
                "classic": {
                    "score": round(classic_score),
                    "change_1d": classic_change_1d,
                    "change_1w": classic_change_1w,
                },
                "narrative": {
                    "score": round(narrative_score),
                    "change_1d": narrative_change_1d,
                    "change_1w": narrative_change_1w,
                },
                "positioning": {
                    "score": round(positioning_score),
                    "change_1d": positioning_change_1d,
                    "change_1w": positioning_change_1w,
                },
                "confidence": round(confidence),
                "explanation": explanation
                or f"Markets are {regime_label.lower()}, with balanced indicators.",
                "components": components or [],
                "data_quality": data_quality or {},
            },
        }

        return payload

    def generate_from_latest(
        self,
        market_id: str,
        store: Any,
    ) -> Dict[str, Any]:
        """Generate a static export from the latest database records.

        Args:
            market_id: Market identifier.
            store: DuckDBStore instance to read from.

        Returns:
            Sanitized export dict.
        """
        from backend.storage.duckdb_store import DuckDBStore

        if not isinstance(store, DuckDBStore):
            raise TypeError("store must be a DuckDBStore instance")

        latest_score = store.get_latest_score(market_id)
        components = store.get_all_components_at_time(market_id)

        if latest_score is None:
            logger.warning("No score found for %s, generating default export", market_id)
            return self.generate_static_export(market_id=market_id)

        return self.generate_static_export(
            market_id=market_id,
            timestamp=latest_score.timestamp,
            composite_score=latest_score.composite_score,
            regime=latest_score.regime.value,
            direction=latest_score.direction,
            classic_score=latest_score.classic_score,
            narrative_score=latest_score.narrative_score,
            positioning_score=latest_score.positioning_score,
            confidence=latest_score.confidence,
            explanation=latest_score.explanation,
            components=components,
            data_quality={
                "overall_confidence": latest_score.data_quality.overall_confidence,
                "sources_used": latest_score.data_quality.sources_used,
                "sources_available": latest_score.data_quality.sources_available,
                "missing_components": latest_score.data_quality.missing_components,
                "freshness_minutes": latest_score.data_quality.data_freshness_minutes,
            },
        )

    # ── Persistence ───────────────────────────────────────────────────────

    def save_export(self, payload: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save an export payload to disk as JSON.

        Args:
            payload: Export dict to save.
            filename: Optional filename. Defaults to {market_id}_latest.json.

        Returns:
            Path to the saved file.
        """
        market_id = payload.get("marketpulse", {}).get("market", "unknown")
        fname = filename or f"{market_id}_latest.json"
        fpath = self.payloads_dir / fname

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        logger.info("Static export saved: %s", fpath)
        return fpath

    def get_latest_export(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Read the latest static export for a market from disk.

        Args:
            market_id: Market identifier.

        Returns:
            The export dict, or None if no export exists.
        """
        fpath = self.payloads_dir / f"{market_id}_latest.json"
        if not fpath.exists():
            return None

        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_exports(self) -> List[str]:
        """List all saved export filenames.

        Returns:
            List of export filenames.
        """
        return sorted(
            f.name
            for f in self.payloads_dir.glob("*_latest.json")
            if f.is_file()
        )

"""ETF flows, fund flows, and futures positioning indicator (stub)."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class FlowsPositioningIndicator:
    """Calculates flows and positioning score (mostly stubs for Tier 2 data).

    Components:
    - ETF flows (stub — needs premium API)
    - Fund flows (stub)
    - Futures positioning CFTC (stub)
    - Options skew (stub)
    - Margin debt (stub)
    """

    def __init__(self):
        self.name = "flows_positioning"
        self.description = "ETF flows, fund flows, and futures positioning"

    async def calculate(
        self,
        provider_chain: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate flows/positioning score."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="composite",
            available=False,
            direction="neutral",
            description="Flows/positioning data not yet available (stub)",
            data_source="premium_providers",
            invert=False,
        )

    def calculate_sync(
        self,
        etf_flows: Optional[List[float]] = None,
        fund_flows: Optional[List[float]] = None,
    ) -> Optional[float]:
        """Synchronous calculation from flows data."""
        # Stub — would combine ETF flows, fund flows, COT data, etc.
        if etf_flows is None and fund_flows is None:
            return None
        return 50.0

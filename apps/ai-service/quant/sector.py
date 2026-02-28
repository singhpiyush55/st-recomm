"""
Sector ETF ranking by 1-month return.
Input: none (or optional ETF list).
Output: list of SectorRanking models sorted by return.
"""

from __future__ import annotations

from data.fetcher import SECTOR_ETFS, get_sector_etf_data
from models.schemas import SectorRanking


def rank_sectors(days: int = 30) -> list[SectorRanking]:
    """
    Download 1-month price data for sector ETFs, compute return %,
    and return a sorted list from highest to lowest.
    """
    etfs = list(SECTOR_ETFS.values())
    df = get_sector_etf_data(etfs, days)

    if df.empty:
        return []

    # Build name→etf reverse map
    etf_to_sector = {v: k for k, v in SECTOR_ETFS.items()}

    rankings: list[SectorRanking] = []

    for etf in etfs:
        if etf not in df.columns:
            continue

        prices = df[etf].dropna()
        if len(prices) < 2:
            continue

        first_price = float(prices.iloc[0])
        last_price = float(prices.iloc[-1])

        if first_price == 0:
            continue

        return_pct = ((last_price - first_price) / first_price) * 100.0

        rankings.append(
            SectorRanking(
                sector=etf_to_sector.get(etf, etf),
                etf=etf,
                return_1m=round(return_pct, 2),
                rank=0,  # Will be set after sorting
            )
        )

    # Sort by return descending and assign ranks
    rankings.sort(key=lambda r: r.return_1m, reverse=True)
    for i, r in enumerate(rankings):
        r.rank = i + 1

    return rankings


def get_top_sectors(n: int = 3, days: int = 30) -> list[str]:
    """Return the names of the top-N performing sectors."""
    rankings = rank_sectors(days)
    return [r.sector for r in rankings[:n]]

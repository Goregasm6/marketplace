"""Confidence scoring for valuation estimates."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Sequence


def calculate_confidence(
    *, match_scores: Sequence[float], prices: Sequence[float], recognized: bool
) -> float:
    """Combine sample size, match quality, and price agreement into a 0..1 score."""
    if not prices or not match_scores:
        return 0.0
    sample_score = min(len(prices), 5) / 5
    quality_score = mean(match_scores)
    average_price = mean(prices)
    variation = (
        pstdev(prices) / average_price if len(prices) > 1 and average_price else 1.0
    )
    consistency_score = max(0.0, 1.0 - min(variation, 1.0))
    recognition_score = 1.0 if recognized else 0.45
    return round(
        min(
            1.0,
            0.20 * sample_score
            + 0.40 * quality_score
            + 0.25 * consistency_score
            + 0.15 * recognition_score,
        ),
        2,
    )

import pandas as pd

from src.fa_engine import FundamentalSummary
from src.strategy_engine import StrategyResult, rank_strategies, score_for_strategy
from src.ta_engine import compute_indicators


def _sample_enriched_df() -> pd.DataFrame:
    """Return a compute_indicators-enriched sample DataFrame."""
    idx = pd.date_range("2023-01-01", periods=60, freq="B")
    base = pd.Series(range(60), index=idx, dtype=float) + 100
    df = pd.DataFrame(index=idx)
    df["open"] = base
    df["close"] = base + 1
    df["high"] = df["close"] + 0.5
    df["low"] = df["open"] - 0.5
    df["volume"] = 1_000_000
    return compute_indicators(df)


def _sample_fundamentals() -> FundamentalSummary:
    return FundamentalSummary(
        ticker="TEST",
        metrics={"roe": 20.0, "pe_ratio": 15.0, "debt_to_equity": 0.5,
                 "sales_growth_3y": 12.0, "profit_growth_3y": 18.0},
        score=65.0,
        strengths=["ROE above 18% indicates efficient capital use"],
        risks=[],
    )


def test_score_for_strategy_returns_strategy_result():
    df = _sample_enriched_df()
    result = score_for_strategy("TEST", "breakout", df, _sample_fundamentals())
    assert isinstance(result, StrategyResult)
    assert result.ticker == "TEST"
    assert result.strategy == "breakout"
    assert 0 <= result.score <= 100
    assert result.entry > 0
    assert result.stop < result.entry
    assert result.target > result.entry


def test_score_for_strategy_swing():
    df = _sample_enriched_df()
    result = score_for_strategy("TEST", "swing", df, _sample_fundamentals())
    assert result.strategy == "swing"
    assert result.target > result.stop


def test_rank_strategies_returns_sorted_list():
    df = _sample_enriched_df()
    results = rank_strategies("TEST", df, _sample_fundamentals())
    assert len(results) == 3  # breakout, swing, intraday
    # Should be sorted by score descending
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_strategy_result_has_reasons():
    df = _sample_enriched_df()
    result = score_for_strategy("TEST", "breakout", df, _sample_fundamentals())
    assert len(result.reasons) >= 2  # At least TA and FA scores
    assert any("TA score" in r for r in result.reasons)
    assert any("FA score" in r for r in result.reasons)

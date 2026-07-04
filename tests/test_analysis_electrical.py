from __future__ import annotations

import pandas as pd

from ade_insight.analysis.electrical import _cycle_stats


def test_cycle_stats_counts_starts_and_durations():
    df = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=6, freq="60s", tz="Europe/London"),
            "power_W": [0.0, 100.0, 120.0, 0.0, 110.0, 0.0],
        }
    )

    stats = _cycle_stats(
        df,
        compressor_on_threshold_w=50.0,
        compressor_off_threshold_w=40.0,
    )

    assert stats.starts == 2
    assert round(stats.starts_per_hour, 2) == 24.0
    assert stats.mean_on_seconds == 90.0
    assert stats.mean_off_seconds == 60.0

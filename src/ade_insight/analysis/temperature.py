from __future__ import annotations

from dataclasses import asdict, dataclass
import datetime as dt
import json
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from ade_insight.core.temp_plots import plot_ambient_twin_axis, plot_foodstuff_temps
from ade_insight.core.temp_stats import (
    compute_column_stats,
    detect_ambient_columns,
    detect_foodstuff_columns,
)
from ade_insight.io.temp_csv import parse_temp_rh_csv


@dataclass(frozen=True)
class TemperatureAnalysisResult:
    run_dir: Path
    results_dir: Path
    summary_path: Path
    stats_path: Path
    parsed_data_path: Path
    plots: dict[str, str | None]
    summary: dict[str, Any]


def _numeric_columns(df: pd.DataFrame, *, exclude: set[str]) -> list[str]:
    cols: list[str] = []
    for col in df.columns:
        if str(col) in exclude:
            continue
        if pd.to_numeric(df[col], errors="coerce").notna().any():
            cols.append(str(col))
    return cols


def _overall_stats(df: pd.DataFrame, columns: Sequence[str]) -> dict[str, float | None]:
    cols = [c for c in columns if c in df.columns]
    if not cols:
        return {"min": None, "mean": None, "max": None}
    values = df[cols].apply(pd.to_numeric, errors="coerce")
    stacked = values.stack().dropna()
    if stacked.empty:
        return {"min": None, "mean": None, "max": None}
    return {
        "min": float(stacked.min()),
        "mean": float(stacked.mean()),
        "max": float(stacked.max()),
    }


def _time_summary(df: pd.DataFrame) -> dict[str, Any]:
    if "time" not in df.columns or df.empty:
        return {"start": None, "end": None, "duration_hours": 0.0, "median_dt_seconds": None}

    time = pd.to_datetime(df["time"], errors="coerce").dropna()
    if time.empty:
        return {"start": None, "end": None, "duration_hours": 0.0, "median_dt_seconds": None}

    start = time.min()
    end = time.max()
    diffs = time.diff().dropna()
    median_dt = float(diffs.median().total_seconds()) if len(diffs) else None
    duration_h = float((end - start).total_seconds() / 3600.0) if end >= start else 0.0

    return {
        "start": str(start),
        "end": str(end),
        "duration_hours": duration_h,
        "median_dt_seconds": median_dt,
    }


def analyse_temperature(
    *,
    temp_file: Path,
    out_dir: Path,
    tz: str = "Europe/London",
    numeric_time_is_utc: bool = True,
    time_base: str = "auto",
    probe_columns: Sequence[str] | None = None,
    ambient_temp_col: str | None = None,
    ambient_rh_col: str | None = None,
    stamp: str | None = None,
) -> TemperatureAnalysisResult:
    stamp = stamp or dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_dir / stamp
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    df, parse_report = parse_temp_rh_csv(
        temp_file,
        tz=tz,
        numeric_time_is_utc=numeric_time_is_utc,
        time_base=time_base,
    )

    detected_food = detect_foodstuff_columns(df)
    numeric_cols = _numeric_columns(df, exclude={"time"})
    selected_probes = [str(c) for c in (probe_columns or detected_food or numeric_cols)]
    selected_probes = [c for c in selected_probes if c in df.columns]

    amb_t, amb_rh = detect_ambient_columns(
        df,
        ambient_temp_hint=ambient_temp_col,
        ambient_rh_hint=ambient_rh_col,
    )

    parsed_data_path = results_dir / "temperature_data.csv"
    df.to_csv(parsed_data_path, index=False)

    stats = compute_column_stats(df, selected_probes)
    stats_path = results_dir / "temperature_stats.csv"
    stats.to_csv(stats_path, index=False)

    plots: dict[str, str | None] = {"probes": None, "ambient": None}
    if selected_probes:
        probes_plot = plot_foodstuff_temps(
            df,
            selected_probes,
            results_dir / "temperature_probes.png",
            title="",
        )
        plots["probes"] = str(probes_plot)

    if amb_t and amb_rh:
        ambient_plot = plot_ambient_twin_axis(
            df,
            results_dir / "ambient_temperature_rh.png",
            ambient_temp_col=amb_t,
            ambient_rh_col=amb_rh,
            title="",
        )
        plots["ambient"] = str(ambient_plot)

    summary: dict[str, Any] = {
        "analysis_type": "temperature",
        "input_file": str(temp_file),
        "tz": tz,
        "time": _time_summary(df),
        "parse_report": asdict(parse_report),
        "columns": {
            "numeric": numeric_cols,
            "selected_probes": selected_probes,
            "ambient_temp": amb_t,
            "ambient_rh": amb_rh,
        },
        "overall": _overall_stats(df, selected_probes),
        "plots": plots,
    }

    summary_path = results_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return TemperatureAnalysisResult(
        run_dir=run_dir,
        results_dir=results_dir,
        summary_path=summary_path,
        stats_path=stats_path,
        parsed_data_path=parsed_data_path,
        plots=plots,
        summary=summary,
    )

from __future__ import annotations

from dataclasses import asdict, dataclass
import datetime as dt
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ade_insight.core.energy import EnergyResults, compute_energy_results
from ade_insight.core.plots import plot_power, plot_voltage_current
from ade_insight.io.power_txt import parse_power_txt_si


@dataclass(frozen=True)
class CycleStats:
    starts: int
    starts_per_hour: float
    mean_on_seconds: float
    mean_off_seconds: float


@dataclass(frozen=True)
class ElectricalAnalysisResult:
    run_dir: Path
    results_dir: Path
    summary_path: Path
    parsed_data_path: Path
    energy_results_path: Path
    plots: dict[str, str | None]
    summary: dict[str, Any]


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


def _cycle_stats(
    df: pd.DataFrame,
    *,
    compressor_on_threshold_w: float,
    compressor_off_threshold_w: float,
) -> CycleStats:
    if "power_W" not in df.columns or "time" not in df.columns or df.empty:
        return CycleStats(0, 0.0, float("nan"), float("nan"))

    data = df[["time", "power_W"]].copy()
    data["time"] = pd.to_datetime(data["time"], errors="coerce")
    data["power_W"] = pd.to_numeric(data["power_W"], errors="coerce")
    data = data.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    if data.empty:
        return CycleStats(0, 0.0, float("nan"), float("nan"))

    states: list[bool] = []
    on = False
    for value in data["power_W"]:
        if pd.notna(value):
            if not on and float(value) >= compressor_on_threshold_w:
                on = True
            elif on and float(value) <= compressor_off_threshold_w:
                on = False
        states.append(on)

    starts = 0
    durations: list[tuple[bool, float]] = []
    if len(states) > 1:
        segment_state = states[0]
        segment_start = data["time"].iloc[0]
        previous_state = states[0]
        for idx in range(1, len(states)):
            current_state = states[idx]
            if current_state and not previous_state:
                starts += 1
            if current_state != segment_state:
                segment_end = data["time"].iloc[idx]
                durations.append((segment_state, float((segment_end - segment_start).total_seconds())))
                segment_start = segment_end
                segment_state = current_state
            previous_state = current_state
        final_end = data["time"].iloc[-1]
        durations.append((segment_state, float((final_end - segment_start).total_seconds())))

    duration_h = float((data["time"].iloc[-1] - data["time"].iloc[0]).total_seconds() / 3600.0)
    starts_per_hour = starts / duration_h if duration_h > 0 else 0.0
    on_durations = [seconds for state, seconds in durations if state and seconds > 0]
    off_durations = [seconds for state, seconds in durations if not state and seconds > 0]

    return CycleStats(
        starts=starts,
        starts_per_hour=float(starts_per_hour),
        mean_on_seconds=float(sum(on_durations) / len(on_durations)) if on_durations else float("nan"),
        mean_off_seconds=float(sum(off_durations) / len(off_durations)) if off_durations else float("nan"),
    )


def analyse_electrical(
    *,
    power_file: Path,
    out_dir: Path,
    tz: str = "Europe/London",
    time_offset_seconds: int = 0,
    compressor_on_threshold_w: float = 50.0,
    compressor_off_threshold_w: float | None = None,
    resample_seconds: int | None = None,
    stamp: str | None = None,
) -> ElectricalAnalysisResult:
    stamp = stamp or dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_dir / stamp
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    df = parse_power_txt_si(power_file, tz=tz, time_offset_seconds=time_offset_seconds)
    parsed_data_path = results_dir / "electrical_data.csv"
    df.to_csv(parsed_data_path, index=False)

    off_threshold = (
        float(compressor_off_threshold_w)
        if compressor_off_threshold_w is not None
        else float(compressor_on_threshold_w) * 0.8
    )
    energy: EnergyResults = compute_energy_results(
        df,
        window_name="full_file",
        resample_seconds=resample_seconds,
        compressor_on_threshold_w=compressor_on_threshold_w,
        compressor_off_threshold_w=off_threshold,
    )
    energy_results_path = results_dir / "electrical_results.json"
    energy_results_path.write_text(json.dumps(asdict(energy), indent=2), encoding="utf-8")
    pd.DataFrame([asdict(energy)]).to_csv(results_dir / "electrical_results.csv", index=False)

    cycle_stats = _cycle_stats(
        df,
        compressor_on_threshold_w=compressor_on_threshold_w,
        compressor_off_threshold_w=off_threshold,
    )

    power_plot = plot_power(df, results_dir, prefix="electrical")
    vc_paths = plot_voltage_current(df, results_dir, prefix="electrical")
    plots: dict[str, str | None] = {
        "power": str(power_plot),
        "voltage": str(vc_paths.get("voltage")) if vc_paths.get("voltage") else None,
        "current": str(vc_paths.get("current")) if vc_paths.get("current") else None,
    }

    summary: dict[str, Any] = {
        "analysis_type": "electrical",
        "input_file": str(power_file),
        "tz": tz,
        "time": _time_summary(df),
        "power_results": asdict(energy),
        "cycle_stats": asdict(cycle_stats),
        "plots": plots,
    }
    summary_path = results_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return ElectricalAnalysisResult(
        run_dir=run_dir,
        results_dir=results_dir,
        summary_path=summary_path,
        parsed_data_path=parsed_data_path,
        energy_results_path=energy_results_path,
        plots=plots,
        summary=summary,
    )

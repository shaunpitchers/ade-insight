from __future__ import annotations

from pathlib import Path
from typing import Sequence, Optional

import pandas as pd
import matplotlib.pyplot as plt

from .plot_style import apply_default_rcparams, finalize_and_save, place_legend_below
import numpy as np


def _set_rh_ylim(ax, rh_series):
    """Set RH axis to mean ±10%, clipped to 0–100."""

    rh = pd.to_numeric(rh_series, errors="coerce").dropna()
    if rh.empty:
        ax.set_ylim(0, 100)
        return

    mean_rh = rh.mean()

    lower = max(0, mean_rh - 10)
    upper = min(100, mean_rh + 10)

    if lower == upper:
        lower = max(0, mean_rh - 5)
        upper = min(100, mean_rh + 5)

    ax.set_ylim(lower, upper)


def _set_padded_ylim(ax, series_list, pad_frac: float = 0.08, min_pad: float = 1.0) -> None:
    vals = pd.concat([pd.to_numeric(s, errors="coerce") for s in series_list], axis=0).dropna()
    if vals.empty:
        return
    vmin, vmax = float(vals.min()), float(vals.max())
    if vmin == vmax:
        pad = max(min_pad, abs(vmin) * pad_frac)
        ax.set_ylim(vmin - pad, vmax + pad)
        return
    span = vmax - vmin
    pad = max(min_pad, span * pad_frac)
    ax.set_ylim(vmin - pad, vmax + pad)


def _despike_series(y: pd.Series, *, k: float = 8.0) -> pd.Series:
    """
    Remove occasional high spikes (e.g., startup current captured at 10s sampling).
    Robust rule using MAD around median. Spikes are replaced with NaN (line breaks).
    """
    y_num = pd.to_numeric(y, errors="coerce").astype(float)

    med = np.nanmedian(y_num)
    mad = np.nanmedian(np.abs(y_num - med))

    # If MAD is zero (flat series), do nothing.
    if not np.isfinite(mad) or mad == 0:
        return y_num

    thresh = med + k * mad
    y_num = y_num.mask(y_num > thresh)
    return y_num


def _to_time(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df["time"], errors="coerce")


def plot_power(
    power_aligned: pd.DataFrame,
    out_dir: str | Path,
    *,
    prefix: str = "test_last_24h",
) -> Path:
    """
    Save power plot (power_W vs time).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = power_aligned.copy()
    x = _to_time(df)

    path = out_dir / f"{prefix}_power.png"
    if "power_W" not in df.columns:
        return path

    y = pd.to_numeric(df["power_W"], errors="coerce")
    y = _despike_series(y, k=8.0)

    apply_default_rcparams()
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (W)")
    # No title
    fig.autofmt_xdate()
    finalize_and_save(fig, path)
    return path


def plot_voltage_current(
    power_aligned: pd.DataFrame,
    out_dir: str | Path,
    *,
    prefix: str = "test_last_24h",
) -> dict[str, Path]:
    """
    Save voltage and current plots if those columns exist.

    Creates:
      - <prefix>_voltage.png  (if voltage_V exists)
      - <prefix>_current.png  (if current_A exists)
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = power_aligned.copy()
    x = _to_time(df)

    created: dict[str, Path] = {}

    if "voltage_V" in df.columns:
        path = out_dir / f"{prefix}_voltage.png"
        apply_default_rcparams()
        fig, ax = plt.subplots()
        y = _despike_series(df["voltage_V"], k=8.0)
        ax.plot(x, y)
        ax.set_xlabel("Time")
        ax.set_ylabel("Voltage (V)")
        fig.autofmt_xdate()
        finalize_and_save(fig, path)
        created["voltage"] = path

    if "current_A" in df.columns:
        path = out_dir / f"{prefix}_current.png"
        apply_default_rcparams()
        fig, ax = plt.subplots()
        y = _despike_series(df["current_A"], k=8.0)
        ax.plot(x, y)
        ax.set_xlabel("Time")
        ax.set_ylabel("Current (A)")
        fig.autofmt_xdate()
        finalize_and_save(fig, path)
        created["current"] = path

    return created


def plot_foodstuff_lines(
    df: pd.DataFrame,
    food_cols: Sequence[str],
    out_path: str | Path,
    *,
    title: str,
) -> Path:
    """
    Plot all foodstuff probes (multiple lines).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    x = _to_time(df)

    apply_default_rcparams()
    fig, ax = plt.subplots()
    for c in food_cols:
        if c not in df.columns:
            continue
        y = pd.to_numeric(df[c], errors="coerce")
        ax.plot(x, y, label=str(c))

    ax.set_xlabel("Time")
    ax.set_ylabel("Foodstuff temperature (°C)")
    place_legend_below(ax, ncol=4)
    fig.autofmt_xdate()
    finalize_and_save(fig, out_path)
    return out_path


def plot_foodstuff_min_max_mean(
    df: pd.DataFrame,
    food_cols: Sequence[str],
    out_path: str | Path,
    *,
    title: str,
) -> Path:
    """
    Plot min/max/mean across all food probes at each timestamp.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    x = _to_time(df)

    cols = [c for c in food_cols if c in df.columns]
    if not cols:
        return out_path

    values = df[cols].apply(pd.to_numeric, errors="coerce")
    y_min = values.min(axis=1, skipna=True)
    y_max = values.max(axis=1, skipna=True)
    y_mean = values.mean(axis=1, skipna=True)

    apply_default_rcparams()
    fig, ax = plt.subplots()
    ax.plot(x, y_min, label="min")
    ax.plot(x, y_mean, label="mean")
    ax.plot(x, y_max, label="max")
    ax.set_xlabel("Time")
    ax.set_ylabel("Foodstuff temperature (°C)")
    place_legend_below(ax, ncol=3)
    fig.autofmt_xdate()
    finalize_and_save(fig, out_path)
    return out_path


def plot_ambient_temps_and_rh(
    df: pd.DataFrame,
    out_path: str | Path,
    *,
    ta_col: str,
    ground_col: str,
    ceiling_col: str,
    rh_col: str,
    title: str,
) -> Path:
    """
    Twin-axis plot:
      - Left axis: Ta + Ground + Ceiling (°C)
      - Right axis: RH (%)
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    x = _to_time(df)

    ta = pd.to_numeric(df[ta_col], errors="coerce")
    g = pd.to_numeric(df[ground_col], errors="coerce")
    c = pd.to_numeric(df[ceiling_col], errors="coerce")
    rh = pd.to_numeric(df[rh_col], errors="coerce")

    apply_default_rcparams()
    fig, ax1 = plt.subplots()

    l1 = ax1.plot(x, ta, label="Ta")
    l2 = ax1.plot(x, g, label="Ground")
    l3 = ax1.plot(x, c, label="Ceiling")
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Ambient temperature (°C)")
    # Left axis limits from temperature data with padding
    _set_padded_ylim(ax1, [ta, g, c], pad_frac=0.08, min_pad=0.5)

    ax2 = ax1.twinx()
    l4 = ax2.plot(x, rh, label="RH", color="black")  # fixed to black
    ax2.set_ylabel("Relative humidity (%)")
    # Right axis: standard RH range keeps it visually separated and consistent
    _set_rh_ylim(ax2, rh)

    # Combine legends from both axes so RH appears
    lines = l1 + l2 + l3 + l4
    labels = [ln.get_label() for ln in lines]
    ax1.legend(
        lines,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.30),
        ncol=4,
        framealpha=0.9,
    )

    fig.autofmt_xdate()
    finalize_and_save(fig, out_path)
    return out_path

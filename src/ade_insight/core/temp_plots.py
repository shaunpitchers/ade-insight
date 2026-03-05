from __future__ import annotations

from pathlib import Path
from typing import Sequence, Optional

import pandas as pd
import matplotlib.pyplot as plt

from .plot_style import apply_default_rcparams, finalize_and_save, place_legend_below


def _set_rh_ylim(ax, rh_series):
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


def plot_foodstuff_temps(
    df: pd.DataFrame,
    columns: Sequence[str],
    out_path: str | Path,
    *,
    title: str,
) -> Path:
    """
    Single plot with multiple foodstuff probes (1..8).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    x = pd.to_datetime(df["time"], errors="coerce")

    apply_default_rcparams()
    fig, ax = plt.subplots()
    for c in columns:
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


def plot_ambient_twin_axis(
    df: pd.DataFrame,
    out_path: str | Path,
    *,
    ambient_temp_col: str,
    ambient_rh_col: str,
    title: str,
) -> Path:
    """
    Twin-axis plot for ambient dry bulb and RH over time.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    x = pd.to_datetime(df["time"], errors="coerce")
    t = pd.to_numeric(df[ambient_temp_col], errors="coerce")
    rh = pd.to_numeric(df[ambient_rh_col], errors="coerce")

    apply_default_rcparams()
    fig, ax1 = plt.subplots()
    l1 = ax1.plot(x, t, label="Ambient dry bulb")
    ax1.set_xlabel("Time")
    ax1.set_ylabel(f"Ambient dry bulb (°C) [{ambient_temp_col}]")

    ax2 = ax1.twinx()
    l2 = ax2.plot(x, rh, label="Ambient RH", color="black")
    ax2.set_ylabel(f"Ambient RH (%) [{ambient_rh_col}]")
    # Temperature (left)
    _set_padded_ylim(ax1, [t], pad_frac=0.08, min_pad=0.5)

    # RH (right)
    _set_rh_ylim(ax2, rh)

    # Combined legend so RH is included
    lines = l1 + l2
    labels = [ln.get_label() for ln in lines]
    ax1.legend(
        lines,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.3),
        ncol=2,
        framealpha=0.9,
    )

    fig.autofmt_xdate()
    finalize_and_save(fig, out_path)
    return out_path

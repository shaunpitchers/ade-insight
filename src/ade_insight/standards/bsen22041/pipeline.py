from __future__ import annotations

from pathlib import Path
from typing import Any

from ade_insight.standards.bsen22041.runner import Bsen22041RunResult, run_bsen22041


def _cfg_get(cfg: Any, name: str, default: Any) -> Any:
    if cfg is None:
        return default
    if isinstance(cfg, dict):
        return cfg.get(name, default)
    return getattr(cfg, name, default)


def run_alignment_and_energy(
    temp_file: str | Path,
    power_file: str | Path,
    test_start: str,
    cfg: Any = None,
) -> Bsen22041RunResult:
    """Compatibility wrapper for the BS EN 22041 runner.

    Older callers can pass a lightweight config object or dict. New code should
    call ``run_bsen22041`` directly.
    """
    return run_bsen22041(
        temp_file=Path(temp_file),
        power_file=Path(power_file),
        test_start=test_start,
        out_dir=Path(_cfg_get(cfg, "out_dir", Path("out/inspect"))),
        tz=str(_cfg_get(cfg, "tz", "Europe/London")),
        resample_seconds=int(_cfg_get(cfg, "resample_seconds", 10)),
        prefix=str(_cfg_get(cfg, "prefix", "aligned")),
        compressor_on_threshold_w=float(_cfg_get(cfg, "compressor_on_threshold_w", 50.0)),
        coverage_max_missing_percent=float(_cfg_get(cfg, "coverage_max_missing_percent", 0.5)),
        ta_col=_cfg_get(cfg, "ta_col", None),
        ground_col=_cfg_get(cfg, "ground_col", None),
        ceiling_col=_cfg_get(cfg, "ceiling_col", None),
        rh_col=_cfg_get(cfg, "rh_col", None),
        probe_distance_m=float(_cfg_get(cfg, "probe_distance_m", 2.5)),
        product_name=_cfg_get(cfg, "product_name", None),
    )

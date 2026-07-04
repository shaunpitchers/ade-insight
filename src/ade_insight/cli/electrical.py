from __future__ import annotations

from pathlib import Path

import typer

from ade_insight.analysis.electrical import analyse_electrical

app = typer.Typer(help="Standalone electrical analysis tools")


@app.command("analyse")
def analyse(
    power_file: Path = typer.Argument(..., exists=True, readable=True),
    out_dir: Path = typer.Option(Path("out/electrical"), "--out-dir"),
    tz: str = typer.Option("Europe/London", "--tz"),
    offset: int = typer.Option(0, "--offset", help="Power timestamp offset in seconds"),
    resample_seconds: int | None = typer.Option(
        None,
        "--resample-seconds",
        help="Sample interval for energy integration. Defaults to inferred median dt.",
    ),
    compressor_on_threshold_w: float = typer.Option(50.0, "--compressor-on-threshold-w"),
    compressor_off_threshold_w: float | None = typer.Option(None, "--compressor-off-threshold-w"),
) -> None:
    result = analyse_electrical(
        power_file=power_file,
        out_dir=out_dir,
        tz=tz,
        time_offset_seconds=offset,
        resample_seconds=resample_seconds,
        compressor_on_threshold_w=compressor_on_threshold_w,
        compressor_off_threshold_w=compressor_off_threshold_w,
    )

    typer.echo(f"Output: {result.run_dir}")
    typer.echo(f"Summary: {result.summary_path}")
    pr = result.summary["power_results"]
    cycles = result.summary["cycle_stats"]
    typer.echo(
        f"kWh/day={pr['kwh_per_day']:.3f}, runtime={pr['runtime_percent']:.1f}%, "
        f"mean ON={pr['mean_power_on_w']:.1f} W, mean OFF={pr['mean_power_off_w']:.1f} W"
    )
    typer.echo(
        f"Starts={cycles['starts']}, starts/hour={cycles['starts_per_hour']:.2f}, "
        f"mean ON={cycles['mean_on_seconds']:.0f}s, mean OFF={cycles['mean_off_seconds']:.0f}s"
    )

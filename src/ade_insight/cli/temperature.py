from __future__ import annotations

from pathlib import Path

import typer

from ade_insight.analysis.temperature import analyse_temperature

app = typer.Typer(help="Standalone temperature/RH analysis tools")


@app.command("analyse")
def analyse(
    temp_file: Path = typer.Argument(..., exists=True, readable=True),
    out_dir: Path = typer.Option(Path("out/temperature"), "--out-dir"),
    tz: str = typer.Option("Europe/London", "--tz"),
    time_base: str = typer.Option("auto", "--time-base", help="auto, excel_days, or datetime"),
    numeric_time_is_utc: bool = typer.Option(
        True,
        "--numeric-time-is-utc/--numeric-time-is-local",
        help="How to interpret numeric Excel-day timestamps.",
    ),
    probe_col: list[str] | None = typer.Option(
        None,
        "--probe-col",
        help="Probe column to include. Repeat for multiple columns. Defaults to detected food probes.",
    ),
    ambient_temp_col: str | None = typer.Option(None, "--ambient-temp-col"),
    ambient_rh_col: str | None = typer.Option(None, "--ambient-rh-col"),
) -> None:
    result = analyse_temperature(
        temp_file=temp_file,
        out_dir=out_dir,
        tz=tz,
        numeric_time_is_utc=numeric_time_is_utc,
        time_base=time_base,
        probe_columns=probe_col,
        ambient_temp_col=ambient_temp_col,
        ambient_rh_col=ambient_rh_col,
    )

    typer.echo(f"Output: {result.run_dir}")
    typer.echo(f"Summary: {result.summary_path}")
    typer.echo(f"Stats: {result.stats_path}")
    overall = result.summary.get("overall", {})
    typer.echo(
        "Overall selected probes: "
        f"min={overall.get('min')}, mean={overall.get('mean')}, max={overall.get('max')}"
    )

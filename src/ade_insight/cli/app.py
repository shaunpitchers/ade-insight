from __future__ import annotations

from pathlib import Path
import typer

from ade_insight import __version__
from ade_insight.io.power_txt import parse_power_txt_si
from ade_insight.cli.bsen22041 import app as bsen22041_app
from ade_insight.cli.diagnostics import app as diagnostics_app
from ade_insight.cli.electrical import app as electrical_app
from ade_insight.cli.temperature import app as temperature_app

app = typer.Typer(help="Test report tool")

app.add_typer(bsen22041_app, name="bsen22041")
app.add_typer(temperature_app, name="temperature")
app.add_typer(electrical_app, name="electrical")
app.add_typer(diagnostics_app, name="diagnostics")


@app.command("parse-power")
def parse_power(
    power_file: Path = typer.Argument(..., exists=True, readable=True),
    tz: str = typer.Option(
        "Europe/London", help="Timezone (power timestamps are local clock time)"
    ),
    offset: int = typer.Option(0, help="Time offset seconds"),
) -> None:
    df = parse_power_txt_si(power_file, tz=tz, time_offset_seconds=offset)
    typer.echo(f"Parsed rows: {len(df)} (skipped: {df.attrs.get('skipped_lines')})")
    typer.echo(f"Start: {df['time'].min()}  End: {df['time'].max()}")
    dt = df["time"].diff().dropna()
    if len(dt):
        typer.echo(f"Median dt (s): {dt.median().total_seconds():.1f}")


@app.command()
def version() -> None:
    typer.echo(__version__)


def main() -> None:
    app(prog_name="ade_insight")


if __name__ == "__main__":
    main()

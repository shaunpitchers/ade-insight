from __future__ import annotations

import json
from pathlib import Path

import typer

from ade_insight.diagnostics.refrigeration import RefrigerationSample, analyse_refrigeration_sample
from ade_insight.diagnostics.schematic import annotate_svg_schematic, schematic_values_from_diagnostic
from ade_insight.diagnostics.thermo import RefpropThermoProvider

app = typer.Typer(help="Refrigeration diagnostic tools")


@app.command("refrigeration")
def refrigeration(
    refrigerant: str = typer.Option(..., "--refrigerant", help="REFPROP refrigerant name"),
    suction_pressure_bar_g: float = typer.Option(..., "--suction-pressure-bar-g"),
    liquid_pressure_bar_g: float = typer.Option(..., "--liquid-pressure-bar-g"),
    suction_line_temp_c: float = typer.Option(..., "--suction-line-temp-c"),
    liquid_line_temp_c: float = typer.Option(..., "--liquid-line-temp-c"),
    product_space_temp_c: float | None = typer.Option(None, "--product-space-temp-c"),
    ambient_temp_c: float | None = typer.Option(None, "--ambient-temp-c"),
    evaporator_air_in_c: float | None = typer.Option(None, "--evaporator-air-in-c"),
    evaporator_air_out_c: float | None = typer.Option(None, "--evaporator-air-out-c"),
    condenser_air_in_c: float | None = typer.Option(None, "--condenser-air-in-c"),
    condenser_air_out_c: float | None = typer.Option(None, "--condenser-air-out-c"),
    discharge_temp_c: float | None = typer.Option(None, "--discharge-temp-c"),
    refprop_root: str | None = typer.Option(None, "--refprop-root"),
    out_json: Path = typer.Option(Path("out/diagnostics/refrigeration_summary.json"), "--out-json"),
    schematic_svg: Path | None = typer.Option(None, "--schematic-svg"),
    schematic_out: Path | None = typer.Option(None, "--schematic-out"),
) -> None:
    sample = RefrigerationSample(
        refrigerant=refrigerant,
        suction_pressure_bar_g=suction_pressure_bar_g,
        liquid_pressure_bar_g=liquid_pressure_bar_g,
        suction_line_temp_c=suction_line_temp_c,
        liquid_line_temp_c=liquid_line_temp_c,
        product_space_temp_c=product_space_temp_c,
        ambient_temp_c=ambient_temp_c,
        evaporator_air_in_c=evaporator_air_in_c,
        evaporator_air_out_c=evaporator_air_out_c,
        condenser_air_in_c=condenser_air_in_c,
        condenser_air_out_c=condenser_air_out_c,
        discharge_temp_c=discharge_temp_c,
    )
    thermo = RefpropThermoProvider(refprop_root)
    result = analyse_refrigeration_sample(sample, thermo)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result.__dict__, indent=2), encoding="utf-8")
    typer.echo(f"Summary: {out_json}")

    first = result.findings[0] if result.findings else {}
    typer.echo(f"Finding: {first.get('severity', '').upper()} {first.get('title', '')}")

    if schematic_svg:
        schematic_target = schematic_out or out_json.with_suffix(".svg")
        values = schematic_values_from_diagnostic(result)
        annotate_svg_schematic(
            svg_path=schematic_svg,
            out_path=schematic_target,
            values_by_id=values,
        )
        typer.echo(f"Annotated schematic: {schematic_target}")

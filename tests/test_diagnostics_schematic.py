from __future__ import annotations

from ade_insight.diagnostics.schematic import (
    annotate_svg_schematic,
    schematic_values_from_diagnostic,
)


def test_annotate_svg_schematic_updates_text_and_status(tmp_path):
    src = tmp_path / "schematic.svg"
    src.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<text id="superheat_label">old</text>'
        '<path id="suction_line" style="stroke:#000;fill:none" />'
        '</svg>',
        encoding="utf-8",
    )

    out = annotate_svg_schematic(
        svg_path=src,
        out_path=tmp_path / "annotated.svg",
        values_by_id={"superheat_label": "8.0 K"},
        status_by_id={"suction_line": "warning"},
    )

    text = out.read_text(encoding="utf-8")
    assert "8.0 K" in text
    assert 'data-status="warning"' in text
    assert "stroke:#b83232" in text


def test_schematic_values_from_diagnostic_formats_known_metrics():
    diagnostic = {
        "metrics": {"superheat_k": 7.234, "pressure_ratio": 4.2},
        "findings": [{"severity": "warning", "title": "Possible issue"}],
    }

    values = schematic_values_from_diagnostic(diagnostic)

    assert values["superheat_label"] == "7.2 K"
    assert values["pressure_ratio_label"] == "4.20:1"
    assert values["diagnostic_summary_label"] == "WARNING: Possible issue"

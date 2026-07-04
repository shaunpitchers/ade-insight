from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

STATUS_COLOURS = {
    "ok": "#1f7a3f",
    "notice": "#b7791f",
    "warning": "#b83232",
    "fault": "#8a1c1c",
}

DEFAULT_METRIC_ELEMENT_IDS = {
    "suction_pressure_bar_abs": "suction_pressure_label",
    "liquid_pressure_bar_abs": "liquid_pressure_label",
    "evaporating_temp_c": "evaporating_temp_label",
    "condensing_temp_c": "condensing_temp_label",
    "superheat_k": "superheat_label",
    "subcooling_k": "subcooling_label",
    "pressure_ratio": "pressure_ratio_label",
    "evaporator_air_delta_k": "evaporator_air_delta_label",
    "condenser_air_delta_k": "condenser_air_delta_label",
}


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    for element in root.iter():
        if element.attrib.get("id") == element_id:
            return element
    return None


def _first_text_element(element: ET.Element) -> ET.Element | None:
    if _tag_name(element) in {"text", "tspan"}:
        return element
    for child in element.iter():
        if _tag_name(child) in {"text", "tspan"}:
            return child
    return None


def _set_text_or_data_value(element: ET.Element, value: object) -> None:
    text_element = _first_text_element(element)
    if text_element is None:
        element.set("data-value", str(value))
        return
    text_element.text = str(value)


def _style_dict(style: str | None) -> dict[str, str]:
    if not style:
        return {}
    out: dict[str, str] = {}
    for part in style.split(";"):
        if not part.strip() or ":" not in part:
            continue
        key, value = part.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def _style_string(values: dict[str, str]) -> str:
    return ";".join(f"{key}:{value}" for key, value in values.items())


def _apply_status(element: ET.Element, status: str) -> None:
    element.set("data-status", status)
    colour = STATUS_COLOURS.get(status)
    if not colour:
        return
    style = _style_dict(element.attrib.get("style"))
    tag = _tag_name(element)
    if tag in {"line", "path", "polyline", "polygon"}:
        style["stroke"] = colour
    else:
        style["fill"] = colour
    element.set("style", _style_string(style))


def format_schematic_value(metric: str, value: Any) -> str:
    if value is None:
        return ""
    number = float(value)
    if metric.endswith("_bar_abs"):
        return f"{number:.2f} bar abs"
    if metric.endswith("_temp_c"):
        return f"{number:.1f} °C"
    if metric.endswith("_k"):
        return f"{number:.1f} K"
    if metric == "pressure_ratio":
        return f"{number:.2f}:1"
    return f"{number:.2f}"


def schematic_values_from_diagnostic(
    diagnostic: Any,
    *,
    element_ids: dict[str, str] | None = None,
) -> dict[str, str]:
    ids = element_ids or DEFAULT_METRIC_ELEMENT_IDS
    metrics = diagnostic.metrics if hasattr(diagnostic, "metrics") else diagnostic.get("metrics", {})
    values: dict[str, str] = {}
    for metric, element_id in ids.items():
        if metric in metrics:
            values[element_id] = format_schematic_value(metric, metrics[metric])
    findings = diagnostic.findings if hasattr(diagnostic, "findings") else diagnostic.get("findings", [])
    if findings:
        first = findings[0]
        title = first.get("title", "") if isinstance(first, dict) else getattr(first, "title", "")
        severity = first.get("severity", "") if isinstance(first, dict) else getattr(first, "severity", "")
        values["diagnostic_summary_label"] = f"{severity.upper()}: {title}" if severity else title
    return values


def annotate_svg_schematic(
    *,
    svg_path: Path,
    out_path: Path,
    values_by_id: dict[str, object],
    status_by_id: dict[str, str] | None = None,
) -> Path:
    """Annotate an SVG by element id.

    Text-like elements receive text content. Non-text elements receive data-value.
    Status values are written as data-status and simple fill/stroke colouring.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    for element_id, value in values_by_id.items():
        element = _find_by_id(root, element_id)
        if element is None:
            continue
        _set_text_or_data_value(element, value)

    for element_id, status in (status_by_id or {}).items():
        element = _find_by_id(root, element_id)
        if element is None:
            continue
        _apply_status(element, status)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path

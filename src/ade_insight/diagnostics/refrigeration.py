from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ade_insight.diagnostics.thermo import ThermoProvider

ATM_PRESSURE_BAR = 1.01325


@dataclass(frozen=True)
class RefrigerationSample:
    refrigerant: str
    suction_pressure_bar_g: float
    liquid_pressure_bar_g: float
    suction_line_temp_c: float
    liquid_line_temp_c: float
    product_space_temp_c: float | None = None
    ambient_temp_c: float | None = None
    evaporator_air_in_c: float | None = None
    evaporator_air_out_c: float | None = None
    condenser_air_in_c: float | None = None
    condenser_air_out_c: float | None = None
    discharge_temp_c: float | None = None


@dataclass(frozen=True)
class RefrigerationMetrics:
    suction_pressure_bar_abs: float
    liquid_pressure_bar_abs: float
    evaporating_temp_c: float
    condensing_temp_c: float
    superheat_k: float
    subcooling_k: float
    pressure_ratio: float
    evaporator_air_delta_k: float | None
    condenser_air_delta_k: float | None
    evaporator_approach_k: float | None
    condenser_approach_k: float | None


@dataclass(frozen=True)
class DiagnosticFinding:
    code: str
    severity: str
    title: str
    detail: str


@dataclass(frozen=True)
class RefrigerationDiagnosticResult:
    sample: dict[str, Any]
    metrics: dict[str, Any]
    findings: list[dict[str, str]]


def gauge_bar_to_abs_bar(value_bar_g: float, *, atmospheric_bar: float = ATM_PRESSURE_BAR) -> float:
    return float(value_bar_g) + float(atmospheric_bar)


def _delta(inlet: float | None, outlet: float | None) -> float | None:
    if inlet is None or outlet is None:
        return None
    return float(inlet) - float(outlet)


def _positive_delta(outlet: float | None, inlet: float | None) -> float | None:
    if inlet is None or outlet is None:
        return None
    return float(outlet) - float(inlet)


def compute_refrigeration_metrics(
    sample: RefrigerationSample,
    thermo: ThermoProvider,
) -> RefrigerationMetrics:
    suction_abs_bar = gauge_bar_to_abs_bar(sample.suction_pressure_bar_g)
    liquid_abs_bar = gauge_bar_to_abs_bar(sample.liquid_pressure_bar_g)
    if suction_abs_bar <= 0 or liquid_abs_bar <= 0:
        raise ValueError("Absolute pressures must be greater than zero.")

    evaporating_temp_c = thermo.saturation_temperature_c(
        refrigerant=sample.refrigerant,
        pressure_kpa_abs=suction_abs_bar * 100.0,
        quality=1.0,
    )
    condensing_temp_c = thermo.saturation_temperature_c(
        refrigerant=sample.refrigerant,
        pressure_kpa_abs=liquid_abs_bar * 100.0,
        quality=0.0,
    )

    evap_air_delta = _delta(sample.evaporator_air_in_c, sample.evaporator_air_out_c)
    condenser_air_delta = _positive_delta(sample.condenser_air_out_c, sample.condenser_air_in_c)
    evap_approach = (
        float(sample.evaporator_air_out_c) - evaporating_temp_c
        if sample.evaporator_air_out_c is not None
        else None
    )
    condenser_approach = (
        condensing_temp_c - float(sample.condenser_air_in_c)
        if sample.condenser_air_in_c is not None
        else None
    )

    return RefrigerationMetrics(
        suction_pressure_bar_abs=suction_abs_bar,
        liquid_pressure_bar_abs=liquid_abs_bar,
        evaporating_temp_c=evaporating_temp_c,
        condensing_temp_c=condensing_temp_c,
        superheat_k=float(sample.suction_line_temp_c) - evaporating_temp_c,
        subcooling_k=condensing_temp_c - float(sample.liquid_line_temp_c),
        pressure_ratio=liquid_abs_bar / suction_abs_bar,
        evaporator_air_delta_k=evap_air_delta,
        condenser_air_delta_k=condenser_air_delta,
        evaporator_approach_k=evap_approach,
        condenser_approach_k=condenser_approach,
    )


def diagnose_refrigeration(metrics: RefrigerationMetrics) -> list[DiagnosticFinding]:
    findings: list[DiagnosticFinding] = []

    if metrics.superheat_k > 14 and metrics.subcooling_k < 3:
        findings.append(
            DiagnosticFinding(
                code="possible_low_charge",
                severity="warning",
                title="Possible low refrigerant charge",
                detail="High superheat with low subcooling is consistent with low charge or starvation.",
            )
        )
    if metrics.superheat_k < 3 and metrics.subcooling_k > 12:
        findings.append(
            DiagnosticFinding(
                code="possible_overcharge",
                severity="warning",
                title="Possible overcharge",
                detail="Low superheat with high subcooling is consistent with overcharge or excess liquid backing up.",
            )
        )
    if metrics.superheat_k > 14 and metrics.subcooling_k > 8:
        findings.append(
            DiagnosticFinding(
                code="possible_liquid_line_restriction",
                severity="warning",
                title="Possible liquid-line restriction",
                detail="High superheat with normal/high subcooling can indicate a restriction, drier issue, or metering fault.",
            )
        )
    if metrics.evaporator_air_delta_k is not None and metrics.evaporator_air_delta_k < 2:
        findings.append(
            DiagnosticFinding(
                code="low_evaporator_air_delta",
                severity="notice",
                title="Low evaporator air temperature drop",
                detail="A small evaporator air delta can indicate airflow, load, control, or refrigerant-side issues.",
            )
        )
    if metrics.condenser_air_delta_k is not None and metrics.condenser_air_delta_k > 18:
        findings.append(
            DiagnosticFinding(
                code="high_condenser_air_delta",
                severity="warning",
                title="High condenser air temperature rise",
                detail="A high condenser air delta can indicate restricted airflow or elevated heat rejection load.",
            )
        )
    if metrics.pressure_ratio > 8:
        findings.append(
            DiagnosticFinding(
                code="high_pressure_ratio",
                severity="warning",
                title="High pressure ratio",
                detail="High compression ratio can indicate high condensing pressure, low suction pressure, or compressor stress.",
            )
        )
    if not findings:
        findings.append(
            DiagnosticFinding(
                code="no_rule_triggered",
                severity="ok",
                title="No rule-based diagnostic triggered",
                detail="Calculated metrics did not cross the configured diagnostic thresholds.",
            )
        )

    return findings


def analyse_refrigeration_sample(
    sample: RefrigerationSample,
    thermo: ThermoProvider,
) -> RefrigerationDiagnosticResult:
    metrics = compute_refrigeration_metrics(sample, thermo)
    findings = diagnose_refrigeration(metrics)
    return RefrigerationDiagnosticResult(
        sample=asdict(sample),
        metrics=asdict(metrics),
        findings=[asdict(finding) for finding in findings],
    )

from __future__ import annotations

from ade_insight.diagnostics.refrigeration import (
    RefrigerationSample,
    analyse_refrigeration_sample,
    gauge_bar_to_abs_bar,
)


class FakeThermoProvider:
    def saturation_temperature_c(
        self,
        *,
        refrigerant: str,
        pressure_kpa_abs: float,
        quality: float,
    ) -> float:
        if quality == 1.0:
            return -10.0
        return 40.0


def test_gauge_bar_to_abs_bar_adds_atmospheric_pressure():
    assert round(gauge_bar_to_abs_bar(2.0), 5) == 3.01325


def test_refrigeration_analysis_flags_low_charge_pattern():
    sample = RefrigerationSample(
        refrigerant="R290",
        suction_pressure_bar_g=1.0,
        liquid_pressure_bar_g=9.0,
        suction_line_temp_c=8.0,
        liquid_line_temp_c=38.0,
    )

    result = analyse_refrigeration_sample(sample, FakeThermoProvider())

    assert result.metrics["superheat_k"] == 18.0
    assert result.metrics["subcooling_k"] == 2.0
    assert result.findings[0]["code"] == "possible_low_charge"

from __future__ import annotations

from typing import Protocol


class ThermoProvider(Protocol):
    def saturation_temperature_c(
        self,
        *,
        refrigerant: str,
        pressure_kpa_abs: float,
        quality: float,
    ) -> float:
        """Return saturation temperature in deg C for pressure and vapour quality."""


class RefpropUnavailableError(RuntimeError):
    pass


class RefpropThermoProvider:
    """Small adapter around the REFPROP Python bindings.

    The rest of ADE Insight depends on the ThermoProvider protocol, not REFPROP
    directly. This keeps diagnostics testable on machines without REFPROP.
    """

    def __init__(self, refprop_root: str | None = None) -> None:
        try:
            from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
        except Exception as exc:  # pragma: no cover - depends on local REFPROP install
            raise RefpropUnavailableError(
                "ctREFPROP is not installed or REFPROP is not configured."
            ) from exc

        if refprop_root is None:
            import os

            refprop_root = os.environ.get("RPPREFIX") or os.environ.get("REFPROP_PATH")

        if not refprop_root:
            raise RefpropUnavailableError(
                "REFPROP root not configured. Set RPPREFIX or REFPROP_PATH."
            )

        self._rp = REFPROPFunctionLibrary(refprop_root)
        self._rp.SETPATHdll(refprop_root)

    def saturation_temperature_c(
        self,
        *,
        refrigerant: str,
        pressure_kpa_abs: float,
        quality: float,
    ) -> float:
        result = self._rp.REFPROPdll(
            refrigerant,
            "PQ",
            "T",
            self._rp.MASS_BASE_SI,
            0,
            0,
            float(pressure_kpa_abs),
            float(quality),
            [1.0],
        )
        if getattr(result, "ierr", 0):
            raise RuntimeError(getattr(result, "herr", "REFPROP saturation call failed"))
        return float(result.Output[0]) - 273.15

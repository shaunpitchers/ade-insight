from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProductSpec:
    name: str
    width_mm: int
    depth_mm: int
    height_mm: int
    net_volume_l: float  # litres


# TODO: Fill these with your real dimensions + volumes
PRODUCTS: dict[str, ProductSpec] = {
    "VCS": ProductSpec("VCS", width_mm=1100, depth_mm=700, height_mm=397, net_volume_l=86.0),
    "VCR": ProductSpec("VCR", width_mm=880, depth_mm=885, height_mm=397, net_volume_l=86.0),
    "VCC": ProductSpec("VCC", width_mm=450, depth_mm=800, height_mm=890, net_volume_l=69.0),
    "VLS": ProductSpec("VLS", width_mm=1100, depth_mm=700, height_mm=349, net_volume_l=65.0),
}


def classify_cabinet_by_food_mean(food_mean_c: float | None) -> str | None:
    """
    Simple robust classification:
      - freezer if mean food temp < -5°C
      - fridge otherwise
    """
    if food_mean_c is None:
        return None
    try:
        v = float(food_mean_c)
    except Exception:
        return None
    if v != v:  # NaN
        return None
    return "freezer" if v < -5.0 else "fridge"


def saec_constants(cabinet_class: str) -> tuple[float, float]:
    """
    SAEC = M*volume + N
    """
    if cabinet_class == "freezer":
        return 5.840, 2380.0
    # default fridge
    return 2.555, 1790.0


def compute_energy_label(eei_percent: float) -> str:
    """
    Bands (per your spec):
      A+  : < 15%
      A   : >=15 and <25
      B   : >=25 and <35
      C   : >=35 and <50
      D   : >=50
    """
    if eei_percent < 15.0:
        return "A+"
    if eei_percent < 25.0:
        return "A"
    if eei_percent < 35.0:
        return "B"
    if eei_percent < 50.0:
        return "C"
    return "D"

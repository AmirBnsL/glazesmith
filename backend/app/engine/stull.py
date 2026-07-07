"""
Stull Triaxial Chart calculator.

Maps SiO2 and Al2O3 molar values to Stull chart coordinates and
classifies the glaze zone (glossy, matte, crazing, etc).
"""

from ..models.schemas import StullCoordinates


def calculate_stull(sio2_mol: float, al2o3_mol: float) -> StullCoordinates:
    ratio = sio2_mol / max(al2o3_mol, 0.001)

    if ratio > 10.0:
        zone = "glossy_stable"
    elif ratio > 8.0:
        zone = "glossy"
    elif ratio > 6.0:
        zone = "satin"
    elif ratio > 4.0:
        zone = "matte"
    elif ratio > 2.0:
        zone = "matte_crawling_risk"
    else:
        zone = "extreme_failure"

    if sio2_mol > 4.0 and ratio < 6.0:
        zone = "crazing_boundary"

    return StullCoordinates(
        x_alumina=round(al2o3_mol, 3),
        y_silica=round(sio2_mol, 3),
        classification_zone=zone,
    )

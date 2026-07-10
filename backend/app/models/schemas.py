from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal


class RecipeIngredient(BaseModel):
    material: str
    percentage: float = Field(ge=0, le=100)


class PredictRequest(BaseModel):
    target_cone: int = Field(default=6, ge=1, le=14)
    atmosphere: str = Field(default="oxidation", pattern="^(oxidation|reduction)$")
    clay_body: str = Field(default="stoneware_buff")
    recipe: list[RecipeIngredient]

    @model_validator(mode="after")
    def check_total(self):
        total = sum(i.percentage for i in self.recipe)
        if abs(total - 100.0) > 1.0:
            raise ValueError(f"Recipe percentages must sum to 100 (got {total:.1f})")
        return self


class UnityMolecularFormula(BaseModel):
    fluxes: dict[str, float]
    stabilizers: dict[str, float]
    formers: dict[str, float]
    others: dict[str, float] = Field(default_factory=dict)


class CalculatedRatios(BaseModel):
    silica_alumina_ratio: float


class UMFAnalysis(BaseModel):
    unity_molecular_formula: UnityMolecularFormula
    calculated_ratios: CalculatedRatios


class RecipeAdjustment(BaseModel):
    material: str
    delta_percentage: float
    action: Literal["increase", "decrease", "introduce", "remove"]
    verified_cte: Optional[float] = None
    verified_surface: Optional[str] = None
    verified_transparency: Optional[str] = None
    verified_crazing_risk: Optional[float] = None
    recommendation: Optional[str] = None


class Remediation(BaseModel):
    chemical_analysis: str
    recipe_adjustments: list[RecipeAdjustment]
    expected_new_cte: float
    verification_summary: Optional[str] = None


class StullCoordinates(BaseModel):
    x_alumina: float
    y_silica: float
    classification_zone: str


class NeighbourInfo(BaseModel):
    rank: int
    cosine_similarity: float
    recipe_name: str
    surface: str
    transparency: str
    color_family: str
    community_notes: str


class OptimizerIngredient(BaseModel):
    material: str
    percentage: float


class OptimizerCandidate(BaseModel):
    recipe: list[OptimizerIngredient]
    stress_delta: float
    surface_class: str
    surface_confidence: float
    score: float


class GlazeMetrics(BaseModel):
    original_cte: float
    target_cte_max: float
    crazing_risk: float
    finish: str
    transparency: str
    color_family: str


class PredictResponse(BaseModel):
    status: str
    timestamp: str
    metrics: GlazeMetrics
    stull_coordinates: StullCoordinates
    remediation: Remediation
    render_output_url: str = ""
    nearest_neighbours: list[NeighbourInfo] = Field(default_factory=list)
    optimizer_candidates: list[OptimizerCandidate] = Field(default_factory=list)

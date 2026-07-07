export interface RecipeIngredient {
  material: string;
  percentage: number;
}

export interface PredictRequest {
  target_cone: number;
  atmosphere: "oxidation" | "reduction";
  clay_body: string;
  recipe: RecipeIngredient[];
}

export interface RecipeAdjustment {
  material: string;
  delta_percentage: number;
  action: "increase" | "decrease" | "introduce" | "remove";
}

export interface Remediation {
  chemical_analysis: string;
  recipe_adjustments: RecipeAdjustment[];
  expected_new_cte: number;
}

export interface StullCoordinates {
  x_alumina: number;
  y_silica: number;
  classification_zone: string;
}

export interface PredictResponse {
  status: string;
  timestamp: string;
  metrics: {
    original_cte: number;
    target_cte_max: number;
    crazing_risk: number;
    finish: string;
  };
  stull_coordinates: StullCoordinates;
  remediation: Remediation;
  render_output_url: string;
}

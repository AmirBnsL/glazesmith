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
  verified_cte?: number;
  verified_surface?: string;
  verified_transparency?: string;
  verified_crazing_risk?: number;
  recommendation?: "recommended" | "not_recommended" | "unverified";
}

export interface Remediation {
  chemical_analysis: string;
  recipe_adjustments: RecipeAdjustment[];
  expected_new_cte: number;
  verification_summary?: string;
}

export interface StullCoordinates {
  x_alumina: number;
  y_silica: number;
  classification_zone: string;
}

export interface NeighbourInfo {
  rank: number;
  cosine_similarity: number;
  recipe_name: string;
  surface: string;
  transparency: string;
  color_family: string;
  community_notes: string;
}

export interface OptimizerCandidate {
  recipe: RecipeIngredient[];
  stress_delta: number;
  surface_class: string;
  surface_confidence: number;
  score: number;
}

export interface GenerateImageRequest {
  surface: string;
  transparency: string;
  color_family: string;
  recipe: { material: string; percentage: number }[];
}

export interface GenerateImageResponse {
  image_url: string;
  success: boolean;
}

export interface PredictResponse {
  status: string;
  timestamp: string;
  metrics: {
    original_cte: number;
    target_cte_max: number;
    crazing_risk: number;
    finish: string;
    transparency: string;
    color_family: string;
  };
  stull_coordinates: StullCoordinates;
  remediation: Remediation;
  render_output_url: string;
  nearest_neighbours: NeighbourInfo[];
  optimizer_candidates?: OptimizerCandidate[];
}

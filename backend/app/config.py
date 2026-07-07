from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fireworks_api_key: str = ""
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    llm_model: str = "accounts/fireworks/models/llama-v3p1-70b-instruct"
    sd_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    gnn_model_path: str = "gnn/glaze_gnn_state.pt"
    glazybench_path: str = "data/glazybench/glazybench.parquet"
    host: str = "0.0.0.0"
    port: int = 8000
    target_cte_stoneware: float = 7.30e-6

    class Config:
        env_file = ".env"


settings = Settings()

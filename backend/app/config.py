from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fireworks_api_key: str = ""
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    llm_model: str = "accounts/fireworks/models/deepseek-v4-flash"
    host: str = "0.0.0.0"
    port: int = 8000
    target_cte_stoneware: float = 7.30e-6
    sdxl_service_url: str = "http://localhost:8001"

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()

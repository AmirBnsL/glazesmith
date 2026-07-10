"""SDXL image generation module.

Calls the standalone SDXL service to generate ceramic glaze visualizations.
Falls back gracefully if the service is unavailable.
"""

import logging
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

SDXL_TIMEOUT = 60.0


def build_glaze_prompt(surface: str, transparency: str, color_family: str, recipe: list[dict]) -> str:
    ingredients = ", ".join(f"{i['material']} {i['percentage']}%" for i in recipe)
    return (
        f"ceramic glaze tile, {surface} finish, {transparency.lower()}, "
        f"{color_family.lower()} color, fired on stoneware clay body, "
        f"ingredients: {ingredients}, studio photography, high detail, 4k"
    )


async def generate_glaze_image(
    surface: str,
    transparency: str,
    color_family: str,
    recipe: list[dict],
) -> str:
    """Call SDXL service to generate a glaze visualization.

    Returns:
        URL to the generated image, or empty string on failure.
    """
    prompt = build_glaze_prompt(surface, transparency, color_family, recipe)
    negative_prompt = "ugly, blurry, low quality, deformed, text, watermark"

    try:
        async with httpx.AsyncClient(timeout=SDXL_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.sdxl_service_url}/generate",
                json={"prompt": prompt, "negative_prompt": negative_prompt},
            )
            resp.raise_for_status()
            data = resp.json()
            image_url = data.get("image_url", "")
            if image_url:
                return f"{settings.sdxl_service_url}{image_url}"
            return ""
    except httpx.TimeoutException:
        logger.warning("SDXL service timed out after %ds", SDXL_TIMEOUT)
        return ""
    except Exception as e:
        logger.warning("SDXL service unavailable: %s", e)
        return ""

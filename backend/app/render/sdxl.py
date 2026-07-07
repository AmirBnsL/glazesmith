"""
Stable Diffusion XL inference engine for glaze image generation.
Runs on AMD ROCm (MI300X).
"""

import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from PIL import Image
import base64
import io
from ..config import settings


class GlazeRenderer:
    def __init__(self):
        self.pipe = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load(self):
        if self.pipe is not None:
            return
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            settings.sd_model_id,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16",
        )
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config
        )
        self.pipe = self.pipe.to(self.device)
        if torch.cuda.is_available():
            self.pipe.enable_model_cpu_offload()

    def build_prompt(self, gnn_prediction: dict) -> tuple[str, str]:
        surface = gnn_prediction.get("predicted_surface_class", "glossy")
        crazing = gnn_prediction.get("crazing_risk_probability", 0.0)
        cte = gnn_prediction.get("coefficient_of_thermal_expansion", 7.0e-6)
        transparency = gnn_prediction.get("transparency_class", "transparent_clear")

        surface_desc = {
            "glossy": "high-gloss reflective silicate glass matrix",
            "satin": "soft satin sheen glass surface",
            "matte": "matte non-reflective fired ceramic surface",
            "crystalline": "crystalline micro-structured glaze surface",
        }.get(surface, "ceramic glaze surface")

        crazing_desc = (
            "distinct hairline crazing crack network throughout the glass layer, "
            "fine crystalline spiderweb fracture pattern, isotropic tensile stress cracking"
            if crazing > 0.3 else
            "smooth intact glass surface with no visible defects"
        )

        cte_note = "high thermal expansion" if cte > 7.5e-6 else "normal thermal expansion"

        prompt = (
            f"Professional studio macro photograph of a fired ceramic test tile, "
            f"{surface_desc}, {transparency} glaze layer, "
            f"{crazing_desc}, {cte_note}, "
            f"kiln fired realistic clay body stoneware buff texture visible underneath, "
            f"high depth of field, sharp detail, natural studio lighting, 8K quality"
        )

        negative = (
            "blurry, low resolution, clip art, 3D render, drawing, "
            "pristine surface, matte paint, rough pottery texture, "
            "cartoon, illustration, painting"
        )

        return prompt, negative

    @torch.inference_mode()
    def generate(self, gnn_prediction: dict) -> str:
        if self.pipe is None:
            self.load()

        prompt, negative = self.build_prompt(gnn_prediction)

        image: Image.Image = self.pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=20,
            guidance_scale=7.5,
            width=512,
            height=512,
        ).images[0]

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{b64}"


renderer = GlazeRenderer()

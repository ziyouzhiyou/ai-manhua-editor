"""
Image Generation API Wrapper
Supports multiple providers: MiMo, Stability AI, Midjourney
"""
import logging
import os
from typing import Dict, Any, Optional
import aiohttp

from src.skills.mimo_api import MiMoAPI

logger = logging.getLogger(__name__)


class ImageGenAPI:
    """
    Unified image generation API
    Automatically selects provider based on config
    """

    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("IMAGE_PROVIDER", "mimo")
        self.mimo_api = MiMoAPI()
        self.stability_key = os.getenv("STABILITY_API_KEY", "")
        self.midjourney_key = os.getenv("MIDJOURNEY_API_KEY", "")

    async def generate(self,
                        prompt: str,
                        size: str = "1024x1024",
                        quality: str = "standard",
                        fast_mode: bool = False,
                        **kwargs) -> Any:
        """
        Generate image using configured provider

        Args:
            prompt: Image generation prompt
            size: Output size
            quality: Quality setting
            fast_mode: Use faster generation
        """
        if self.provider == "mimo":
            return await self._generate_mimo(prompt, size, quality)
        elif self.provider == "stability":
            return await self._generate_stability(prompt, size, quality, fast_mode)
        elif self.provider == "midjourney":
            return await self._generate_midjourney(prompt, size, quality)
        else:
            raise ValueError(f"Unknown image provider: {self.provider}")

    async def _generate_mimo(self, prompt: str, size: str, quality: str) -> Dict:
        """Generate using MiMo API"""
        result = await self.mimo_api.generate_image(
            prompt=prompt,
            size=size,
            quality=quality
        )

        # Extract image URL or data
        if "data" in result and len(result["data"]) > 0:
            return result["data"][0].get("url", "")
        return result

    async def _generate_stability(self, prompt: str, size: str, quality: str, fast_mode: bool) -> bytes:
        """Generate using Stability AI API"""
        width, height = map(int, size.split("x"))

        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30 if fast_mode else 50
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.stability_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Stability API error: {response.status}")

                result = await response.json()
                # Return base64 image data
                if "artifacts" in result:
                    import base64
                    return base64.b64decode(result["artifacts"][0]["base64"])
                return b""

    async def _generate_midjourney(self, prompt: str, size: str, quality: str) -> str:
        """Generate using Midjourney API (placeholder)"""
        # This would integrate with a Midjourney API wrapper
        logger.warning("Midjourney integration not yet implemented")
        raise NotImplementedError("Midjourney API integration coming soon")

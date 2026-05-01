"""
Image Generator Agent
Batch generates images from storyboard frames using AI image APIs
"""
import asyncio
import logging
import os
from typing import Dict, Any, List
from pathlib import Path
import aiohttp
import base64

from src.skills.image_gen_api import ImageGenAPI
from src.skills.mimo_api import MiMoAPI

logger = logging.getLogger(__name__)


class ImageGeneratorAgent:
    """
    Generates images for storyboard frames using AI image generation APIs
    Supports batch processing with concurrency control
    """

    def __init__(self, image_api: ImageGenAPI = None, mimo_api: MiMoAPI = None):
        self.image_api = image_api or ImageGenAPI()
        self.mimo_api = mimo_api or MiMoAPI()
        self.semaphore = asyncio.Semaphore(3)  # Max concurrent image generations

    async def generate(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Generate images for all storyboard frames

        Args:
            config: Task configuration
                - storyboard: Storyboard data with frames
                - batch_size: Number of concurrent generations
                - quality: Image quality setting
                - fast_mode: Skip enhancement for speed
            context: Workflow context
            task_id: Current task ID
        """
        storyboard_data = config.get("storyboard", {})
        batch_size = config.get("batch_size", 4)
        quality = config.get("quality", "high")
        fast_mode = config.get("fast_mode", False)

        frames = storyboard_data.get("frames", [])
        if not frames:
            raise ValueError("No frames in storyboard")

        project_id = context.get("workflow_id", "unknown")
        output_dir = Path(context.get("global_config", {}).get("output_dir", "./output")) / project_id / "images"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating {len(frames)} images, batch_size={batch_size}, quality={quality}")

        # Process frames in batches
        results = []
        for i in range(0, len(frames), batch_size):
            batch = frames[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self._generate_single_image(frame, output_dir, quality, fast_mode, task_id) 
                  for frame in batch],
                return_exceptions=True
            )
            results.extend(batch_results)

            progress = min(100, int((i + len(batch)) / len(frames) * 100))
            logger.info(f"Image generation progress: {progress}%")

        # Collect results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]

        return {
            "images": successful,
            "failed": failed,
            "total_frames": len(frames),
            "successful_count": len(successful),
            "failed_count": len(failed),
            "output_dir": str(output_dir),
            "metadata": {
                "quality": quality,
                "fast_mode": fast_mode,
                "batch_size": batch_size
            }
        }

    async def _generate_single_image(self, frame: Dict, output_dir: Path, 
                                      quality: str, fast_mode: bool, task_id: str) -> Dict[str, Any]:
        """Generate a single image for a frame"""
        async with self.semaphore:
            frame_id = frame.get("id", "unknown")
            prompt = frame.get("image_prompt", "")

            if not prompt:
                logger.warning(f"Empty prompt for frame {frame_id}")
                return {"frame_id": frame_id, "success": False, "error": "Empty prompt"}

            try:
                # Generate image using API
                image_data = await self.image_api.generate(
                    prompt=prompt,
                    size=self._get_image_size(quality),
                    quality=quality,
                    fast_mode=fast_mode
                )

                # Save image
                image_path = output_dir / f"{frame_id}.png"
                if isinstance(image_data, str) and image_data.startswith("http"):
                    # Download from URL
                    await self._download_image(image_data, image_path)
                elif isinstance(image_data, bytes):
                    # Save binary data
                    with open(image_path, "wb") as f:
                        f.write(image_data)
                elif isinstance(image_data, str) and image_data.startswith("data:image"):
                    # Base64 encoded
                    image_data = base64.b64decode(image_data.split(",")[1])
                    with open(image_path, "wb") as f:
                        f.write(image_data)

                logger.info(f"Generated image: {image_path}")

                return {
                    "frame_id": frame_id,
                    "success": True,
                    "image_path": str(image_path),
                    "prompt": prompt,
                    "quality": quality
                }

            except Exception as e:
                logger.error(f"Failed to generate image for frame {frame_id}: {e}")
                return {
                    "frame_id": frame_id,
                    "success": False,
                    "error": str(e),
                    "prompt": prompt
                }

    async def _download_image(self, url: str, path: Path):
        """Download image from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(path, "wb") as f:
                        f.write(await response.read())
                else:
                    raise RuntimeError(f"Failed to download image: {response.status}")

    def _get_image_size(self, quality: str) -> str:
        """Get image size based on quality"""
        sizes = {
            "medium": "1024x1024",
            "high": "1024x1024",
            "ultra": "1536x1536"
        }
        return sizes.get(quality, "1024x1024")

    async def enhance_prompt(self, base_prompt: str, style: str = "anime") -> str:
        """Use LLM to enhance image prompt"""
        system_prompt = """You are an expert AI image prompt engineer. Enhance the given prompt for maximum quality.
Add details about lighting, composition, style, and atmosphere while keeping it coherent."""

        user_prompt = f"Enhance this image prompt for {style} style:

{base_prompt}"

        response = await self.mimo_api.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="mimo-v2.5",
            temperature=0.3,
            max_tokens=500
        )

        return response.strip()

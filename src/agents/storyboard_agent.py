"""
Storyboard Agent
Generates detailed storyboard frames from parsed scenes
"""
import json
import logging
from typing import Dict, Any, List
import uuid

from src.models.schemas import Storyboard, StoryboardFrame, ImageStyle, Scene
from src.skills.mimo_api import MiMoAPI

logger = logging.getLogger(__name__)


class StoryboardAgent:
    """
    Generates cinematic storyboard from parsed script scenes
    Creates detailed image prompts optimized for AI image generation
    """

    def __init__(self, mimo_api: MiMoAPI = None):
        self.mimo_api = mimo_api or MiMoAPI()

    async def generate(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Generate storyboard from parsed scenes

        Args:
            config: Task configuration
                - scenes: Parsed scene data
                - style: Image style (anime, cinematic_anime, etc.)
                - quality: "medium", "high", "ultra"
                - camera_moves: Whether to include camera movement descriptions
            context: Workflow context
            task_id: Current task ID
        """
        scenes_data = config.get("scenes", [])
        style_name = config.get("style", "anime")
        quality = config.get("quality", "high")
        camera_moves = config.get("camera_moves", False)

        if not scenes_data:
            raise ValueError("No scenes data provided")

        style = ImageStyle(style_name)
        project_id = context.get("workflow_id", str(uuid.uuid4()))

        logger.info(f"Generating storyboard: {len(scenes_data)} scenes, style={style.value}, quality={quality}")

        frames = []
        for scene_data in scenes_data:
            scene_frames = await self._generate_scene_frames(
                scene_data, style, quality, camera_moves, len(frames)
            )
            frames.extend(scene_frames)

        storyboard = Storyboard(
            id=f"sb_{project_id}",
            project_id=project_id,
            frames=frames,
            style=style
        )

        return {
            "storyboard": storyboard.to_dict(),
            "frame_count": len(frames),
            "style": style.value,
            "metadata": {
                "total_scenes": len(scenes_data),
                "total_frames": len(frames),
                "average_frames_per_scene": len(frames) / len(scenes_data) if scenes_data else 0
            }
        }

    async def _generate_scene_frames(self, scene_data: Dict, style: ImageStyle, 
                                     quality: str, camera_moves: bool, 
                                     frame_offset: int) -> List[StoryboardFrame]:
        """Generate frames for a single scene"""

        # Use LLM to determine optimal frame count and composition
        system_prompt = """你是一个专业的AI漫剧分镜师。根据场景描述，设计最佳的分镜方案。
对于每个分镜，提供：
1. 分镜描述（画面内容）
2. AI图像生成提示词（英文，详细描述画面构图、角色、表情、背景、光影）
3. 镜头角度
4. 镜头运动（如果有）
5. 持续时间（秒）
6. 转场类型

输出为JSON数组格式。"""

        scene_json = json.dumps(scene_data, ensure_ascii=False)
        user_prompt = f"""请为以下场景设计分镜：

{scene_json}

风格要求：{style.value}
质量等级：{quality}
是否需要镜头运动：{"是" if camera_moves else "否"}

请输出分镜数组。"""

        response = await self.mimo_api.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="mimo-v2.5-reasoning" if quality == "ultra" else "mimo-v2.5",
            temperature=0.4,
            max_tokens=4000
        )

        try:
            frame_data_list = self._extract_json_array(response)
        except Exception as e:
            logger.warning(f"LLM storyboard generation failed, using fallback: {e}")
            frame_data_list = self._fallback_frame_generation(scene_data, style)

        frames = []
        for i, frame_data in enumerate(frame_data_list):
            frame = StoryboardFrame(
                id=f"frame_{frame_offset + i}",
                scene_id=scene_data.get("id", "unknown"),
                frame_number=frame_offset + i + 1,
                description=frame_data.get("description", ""),
                image_prompt=self._optimize_image_prompt(frame_data.get("image_prompt", ""), style, quality),
                camera_angle=frame_data.get("camera_angle", "medium_shot"),
                camera_movement=frame_data.get("camera_movement", "") if camera_moves else "",
                duration=frame_data.get("duration", 3.0),
                transition_type=frame_data.get("transition_type", "cut")
            )
            frames.append(frame)

        return frames

    def _optimize_image_prompt(self, prompt: str, style: ImageStyle, quality: str) -> str:
        """Optimize image prompt for best generation results"""
        style_modifiers = {
            ImageStyle.ANIME: "anime style, manga art, cel-shaded, vibrant colors, clean lines",
            ImageStyle.CINEMATIC_ANIME: "cinematic anime, dramatic lighting, film grain, anime movie quality, detailed background",
            ImageStyle.MANHUA: "Chinese manhua style, ink wash influence, elegant linework, traditional Chinese aesthetics",
            ImageStyle.CHIBI: "chibi style, cute, super deformed, kawaii, colorful",
            ImageStyle.REALISTIC: "photorealistic, detailed, lifelike, high detail, 8k",
            ImageStyle.WATERCOLOR: "watercolor painting, soft edges, artistic, painterly style"
        }

        quality_modifiers = {
            "medium": "good quality",
            "high": "masterpiece, best quality, highly detailed",
            "ultra": "masterpiece, best quality, ultra detailed, 8k, intricate details, professional artwork"
        }

        base_prompt = prompt.strip()
        style_text = style_modifiers.get(style, style_modifiers[ImageStyle.ANIME])
        quality_text = quality_modifiers.get(quality, quality_modifiers["high"])

        # Combine with optimal structure
        optimized = f"{quality_text}, {style_text}, {base_prompt}"

        # Add negative prompt hints
        negative_hints = "low quality, blurry, deformed, bad anatomy, watermark, signature, text"

        return optimized

    def _fallback_frame_generation(self, scene_data: Dict, style: ImageStyle) -> List[Dict]:
        """Fallback frame generation when LLM fails"""
        dialogues = scene_data.get("dialogues", [])
        description = scene_data.get("description", "")
        setting = scene_data.get("setting", "")
        mood = scene_data.get("mood", "")

        frames = []

        # Establishing shot
        frames.append({
            "description": f"Scene establishing shot: {setting}",
            "image_prompt": f"Wide shot of {setting}, {mood} atmosphere, establishing scene",
            "camera_angle": "long_shot",
            "duration": 2.0,
            "transition_type": "fade"
        })

        # Dialogue frames
        for dialogue in dialogues:
            char_name = dialogue.get("character_id", "character")
            text = dialogue.get("text", "")
            emotion = dialogue.get("emotion", "neutral")

            frames.append({
                "description": f"{char_name}: {text[:50]}",
                "image_prompt": f"Close-up of {char_name} with {emotion} expression, saying "{text[:100]}", detailed face, expressive",
                "camera_angle": "close_up",
                "duration": max(2.0, len(text) * 0.15),
                "transition_type": "cut"
            })

        # Scene out
        if len(dialogues) > 0:
            frames.append({
                "description": "Scene ending",
                "image_prompt": f"Fade out scene, {mood} atmosphere, {setting}",
                "camera_angle": "medium_shot",
                "duration": 1.5,
                "transition_type": "fade"
            })

        return frames

    def _extract_json_array(self, text: str) -> List[Dict]:
        """Extract JSON array from text"""
        import re
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        json_match = re.search(r'(\[.*\])', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        raise ValueError("No JSON array found")

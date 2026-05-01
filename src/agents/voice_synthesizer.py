"""
Voice Synthesizer Agent
Generates speech from dialogues using TTS APIs
"""
import asyncio
import logging
import os
from typing import Dict, Any, List
from pathlib import Path

from src.skills.tts_api import TTSAPI
from src.models.schemas import VoiceEmotion

logger = logging.getLogger(__name__)


class VoiceSynthesizerAgent:
    """
    Synthesizes voice for all dialogues in the script
    Supports multi-speaker with emotion and speed control
    """

    def __init__(self, tts_api: TTSAPI = None):
        self.tts_api = tts_api or TTSAPI()
        self.semaphore = asyncio.Semaphore(5)  # Max concurrent TTS

    async def synthesize(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Synthesize voices for all dialogues

        Args:
            config: Task configuration
                - scenes: Scene data with dialogues
                - voice_style: Voice style (natural, dramatic, emotional)
                - language: Language code
                - multi_speaker: Whether to use different voices per character
                - fast_mode: Skip prosody for speed
            context: Workflow context
            task_id: Current task ID
        """
        scenes_data = config.get("scenes", [])
        voice_style = config.get("voice_style", "natural")
        language = config.get("language", "zh")
        multi_speaker = config.get("multi_speaker", False)
        fast_mode = config.get("fast_mode", False)

        if not scenes_data:
            raise ValueError("No scenes data provided")

        project_id = context.get("workflow_id", "unknown")
        output_dir = Path(context.get("global_config", {}).get("output_dir", "./output")) / project_id / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect all dialogues
        all_dialogues = []
        for scene in scenes_data:
            for dialogue in scene.get("dialogues", []):
                all_dialogues.append({
                    **dialogue,
                    "scene_id": scene.get("id", "unknown")
                })

        logger.info(f"Synthesizing {len(all_dialogues)} dialogue segments")

        # Assign voice IDs if multi-speaker
        character_voices = {}
        if multi_speaker:
            character_voices = self._assign_character_voices(all_dialogues)

        # Synthesize all dialogues
        results = await asyncio.gather(
            *[self._synthesize_dialogue(d, output_dir, voice_style, language, 
                                        character_voices, fast_mode, task_id)
              for d in all_dialogues],
            return_exceptions=True
        )

        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]

        # Calculate total audio duration
        total_duration = sum(r.get("duration", 0) for r in successful)

        return {
            "audio_segments": successful,
            "failed": failed,
            "total_segments": len(all_dialogues),
            "successful_count": len(successful),
            "failed_count": len(failed),
            "total_duration": total_duration,
            "output_dir": str(output_dir),
            "character_voices": character_voices,
            "metadata": {
                "voice_style": voice_style,
                "language": language,
                "multi_speaker": multi_speaker,
                "fast_mode": fast_mode
            }
        }

    async def _synthesize_dialogue(self, dialogue: Dict, output_dir: Path,
                                     voice_style: str, language: str,
                                     character_voices: Dict, fast_mode: bool,
                                     task_id: str) -> Dict[str, Any]:
        """Synthesize a single dialogue segment"""
        async with self.semaphore:
            dialogue_id = f"dlg_{dialogue.get('scene_id', 's')}_{hash(dialogue.get('text', '')) % 10000}"
            text = dialogue.get("text", "")
            character_id = dialogue.get("character_id", "default")
            emotion = dialogue.get("emotion", "neutral")
            speed = dialogue.get("speed", 1.0)

            if not text:
                return {"dialogue_id": dialogue_id, "success": False, "error": "Empty text"}

            try:
                # Determine voice ID
                voice_id = character_voices.get(character_id, "default")
                if voice_id == "default":
                    voice_id = self._get_default_voice(language, dialogue.get("gender", "unknown"))

                # Synthesize speech
                audio_data = await self.tts_api.synthesize(
                    text=text,
                    voice_id=voice_id,
                    emotion=emotion,
                    speed=speed,
                    language=language,
                    style=voice_style
                )

                # Save audio
                audio_path = output_dir / f"{dialogue_id}.mp3"
                if isinstance(audio_data, bytes):
                    with open(audio_path, "wb") as f:
                        f.write(audio_data)
                elif isinstance(audio_data, str) and audio_data.startswith("http"):
                    # Download
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(audio_data) as response:
                            with open(audio_path, "wb") as f:
                                f.write(await response.read())

                # Estimate duration (rough calculation: ~5 chars per second for Chinese)
                duration = len(text) / (5 * speed) if language == "zh" else len(text.split()) / (2.5 * speed)

                logger.info(f"Synthesized: {audio_path} ({duration:.1f}s)")

                return {
                    "dialogue_id": dialogue_id,
                    "success": True,
                    "audio_path": str(audio_path),
                    "text": text,
                    "character_id": character_id,
                    "voice_id": voice_id,
                    "emotion": emotion,
                    "duration": duration,
                    "speed": speed
                }

            except Exception as e:
                logger.error(f"TTS failed for {dialogue_id}: {e}")
                return {
                    "dialogue_id": dialogue_id,
                    "success": False,
                    "error": str(e),
                    "text": text,
                    "character_id": character_id
                }

    def _assign_character_voices(self, dialogues: List[Dict]) -> Dict[str, str]:
        """Assign unique voice IDs to characters"""
        characters = set(d.get("character_id", "default") for d in dialogues)

        # Available voice IDs (example for Chinese)
        voice_pool = [
            "zh-CN-XiaoxiaoNeural",  # Female, young
            "zh-CN-YunxiNeural",     # Male, young
            "zh-CN-XiaoyiNeural",    # Female, gentle
            "zh-CN-YunjianNeural",   # Male, mature
            "zh-CN-XiaohanNeural",   # Female, lively
            "zh-CN-YunfengNeural",   # Male, deep
        ]

        character_voices = {}
        for i, char in enumerate(characters):
            character_voices[char] = voice_pool[i % len(voice_pool)]

        return character_voices

    def _get_default_voice(self, language: str, gender: str) -> str:
        """Get default voice for language and gender"""
        defaults = {
            "zh": {
                "female": "zh-CN-XiaoxiaoNeural",
                "male": "zh-CN-YunxiNeural",
                "unknown": "zh-CN-XiaoxiaoNeural"
            },
            "en": {
                "female": "en-US-JennyNeural",
                "male": "en-US-GuyNeural",
                "unknown": "en-US-JennyNeural"
            }
        }

        lang_defaults = defaults.get(language, defaults["zh"])
        return lang_defaults.get(gender.lower(), lang_defaults["unknown"])

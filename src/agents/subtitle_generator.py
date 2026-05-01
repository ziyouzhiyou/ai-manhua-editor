"""
Subtitle Generator Agent
Generates and styles subtitles for the video
"""
import logging
import os
from typing import Dict, Any, List
from pathlib import Path

from src.models.schemas import SubtitleEntry

logger = logging.getLogger(__name__)


class SubtitleGeneratorAgent:
    """
    Generates ASS/SRT subtitles with anime styling
    """

    def __init__(self):
        pass

    async def generate(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Generate subtitles for the video

        Args:
            config: Task configuration
                - video_path: Path to composed video
                - scenes: Scene data with dialogues
                - audio_segments: Audio timing data
                - style: Subtitle style (simple, anime, cinematic)
                - position: Subtitle position
            context: Workflow context
            task_id: Current task ID
        """
        scenes_data = config.get("scenes", [])
        audio_segments = context.get("results", {}).get("synthesize_voices", {}).get("audio_segments", [])
        style = config.get("style", "anime")
        position = config.get("position", "bottom")

        project_id = context.get("workflow_id", "unknown")
        output_dir = Path(context.get("global_config", {}).get("output_dir", "./output")) / project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate subtitle entries
        subtitle_entries = []
        current_time = 0.0

        for scene in scenes_data:
            for dialogue in scene.get("dialogues", []):
                text = dialogue.get("text", "")
                if not text:
                    continue

                # Find matching audio segment for timing
                char_id = dialogue.get("character_id", "")
                audio_seg = next((a for a in audio_segments 
                                  if a.get("character_id") == char_id 
                                  and a.get("text") == text), None)

                duration = audio_seg.get("duration", len(text) * 0.2) if audio_seg else len(text) * 0.2

                entry = SubtitleEntry(
                    id=f"sub_{len(subtitle_entries)}",
                    text=text,
                    start_time=current_time,
                    end_time=current_time + duration,
                    position=position,
                    style=self._get_style_config(style, dialogue)
                )
                subtitle_entries.append(entry)
                current_time += duration + 0.5  # Gap between subtitles

        # Generate ASS file
        ass_path = output_dir / "subtitles.ass"
        self._write_ass_file(subtitle_entries, str(ass_path), style)

        # Also generate SRT
        srt_path = output_dir / "subtitles.srt"
        self._write_srt_file(subtitle_entries, str(srt_path))

        logger.info(f"Generated subtitles: {len(subtitle_entries)} entries")

        return {
            "success": True,
            "subtitle_entries": [e.to_dict() for e in subtitle_entries],
            "ass_path": str(ass_path),
            "srt_path": str(srt_path),
            "entry_count": len(subtitle_entries),
            "total_duration": current_time,
            "style": style
        }

    def _get_style_config(self, style: str, dialogue: Dict) -> Dict[str, Any]:
        """Get style configuration for subtitle"""
        emotion = dialogue.get("emotion", "neutral")

        base_styles = {
            "simple": {
                "font": "Arial",
                "size": 24,
                "color": "#FFFFFF",
                "outline": "#000000",
                "outline_width": 2,
                "alignment": 2
            },
            "anime": {
                "font": "Noto Sans CJK SC",
                "size": 28,
                "color": "#FFFFFF",
                "outline": "#FF69B4",
                "outline_width": 3,
                "alignment": 2,
                "shadow": "#000000",
                "shadow_offset": 2
            },
            "cinematic": {
                "font": "Noto Serif CJK SC",
                "size": 26,
                "color": "#F5F5F5",
                "outline": "#1a1a1a",
                "outline_width": 2,
                "alignment": 2,
                "shadow": "#000000",
                "shadow_offset": 1
            },
            "comic": {
                "font": "Comic Sans MS",
                "size": 30,
                "color": "#FFFF00",
                "outline": "#000000",
                "outline_width": 4,
                "alignment": 2
            }
        }

        style_config = base_styles.get(style, base_styles["anime"]).copy()

        # Adjust based on emotion
        emotion_colors = {
            "happy": "#FFD700",
            "sad": "#87CEEB",
            "angry": "#FF4500",
            "excited": "#FF69B4",
            "scared": "#9370DB",
            "romantic": "#FF69B4"
        }

        if emotion in emotion_colors:
            style_config["color"] = emotion_colors[emotion]

        return style_config

    def _write_ass_file(self, entries: List[SubtitleEntry], path: str, style: str):
        """Write ASS subtitle file"""
        with open(path, "w", encoding="utf-8") as f:
            # Header
            f.write("[Script Info]
")
            f.write("Title: AI Manhua Subtitles
")
            f.write("ScriptType: v4.00+
")
            f.write("WrapStyle: 0
")
            f.write("ScaledBorderAndShadow: yes
")
            f.write("YCbCr Matrix: TV.601

")

            # Styles
            f.write("[V4+ Styles]
")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
")

            style_config = self._get_style_config(style, {})
            f.write(f"Style: Default,{style_config['font']},{style_config['size']},&H00{style_config['color'][1:]},&H000000FF,&H00{style_config['outline'][1:]},&H00000000,0,0,0,0,100,100,0,0,1,{style_config.get('outline_width', 2)},0,{style_config.get('alignment', 2)},10,10,10,1

")

            # Events
            f.write("[Events]
")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
")

            for entry in entries:
                start = self._format_ass_time(entry.start_time)
                end = self._format_ass_time(entry.end_time)
                text = entry.text.replace("
", "\N")
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}
")

    def _write_srt_file(self, entries: List[SubtitleEntry], path: str):
        """Write SRT subtitle file"""
        with open(path, "w", encoding="utf-8") as f:
            for i, entry in enumerate(entries, 1):
                start = self._format_srt_time(entry.start_time)
                end = self._format_srt_time(entry.end_time)
                f.write(f"{i}
")
                f.write(f"{start} --> {end}
")
                f.write(f"{entry.text}

")

    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

"""
Video Editor Agent
Composes final video from images, audio, and subtitles
"""
import asyncio
import logging
import os
from typing import Dict, Any, List
from pathlib import Path
import subprocess
import json

logger = logging.getLogger(__name__)


class VideoEditorAgent:
    """
    Video composition engine using FFmpeg
    Combines images, audio, and subtitles into final video
    """

    def __init__(self):
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"

    async def compose(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Compose video from generated assets

        Args:
            config: Task configuration
                - storyboard: Storyboard with frame timing
                - images: Generated image paths
                - audio_segments: Synthesized audio segments
                - resolution: Output resolution
                - fps: Frame rate
                - transition: Transition type
            context: Workflow context
            task_id: Current task ID
        """
        storyboard_data = config.get("storyboard", {})
        images_data = context.get("results", {}).get("generate_images", {}).get("images", [])
        audio_data = context.get("results", {}).get("synthesize_voices", {}).get("audio_segments", [])

        resolution = config.get("resolution", "1080p")
        fps = config.get("fps", 24)
        transition = config.get("transition", "fade")

        project_id = context.get("workflow_id", "unknown")
        output_dir = Path(context.get("global_config", {}).get("output_dir", "./output")) / project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / "final_video.mp4"

        logger.info(f"Composing video: {resolution}@{fps}fps, {len(images_data)} frames, {len(audio_data)} audio segments")

        try:
            # Build FFmpeg command
            if config.get("mode") == "fix":
                # Fix mode: re-encode with quality improvements
                input_video = config.get("input_video", str(output_path))
                await self._fix_video(input_video, str(output_path), config)
            else:
                # Normal composition
                await self._compose_video(
                    storyboard_data, images_data, audio_data,
                    str(output_path), resolution, fps, transition
                )

            # Get video info
            video_info = await self._get_video_info(str(output_path))

            return {
                "success": True,
                "video_path": str(output_path),
                "video_info": video_info,
                "resolution": resolution,
                "fps": fps,
                "frame_count": len(images_data),
                "audio_segment_count": len(audio_data)
            }

        except Exception as e:
            logger.error(f"Video composition failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "video_path": str(output_path)
            }

    async def _compose_video(self, storyboard: Dict, images: List[Dict], 
                             audio_segments: List[Dict], output_path: str,
                             resolution: str, fps: int, transition: str):
        """Compose video using FFmpeg"""

        # Create concat list for images
        frames = storyboard.get("frames", [])

        # Build image sequence with durations
        image_list_path = Path(output_path).parent / "image_list.txt"
        with open(image_list_path, "w") as f:
            for i, frame in enumerate(frames):
                # Find matching image
                frame_id = frame.get("id", "")
                image = next((img for img in images if img.get("frame_id") == frame_id), None)

                if image and image.get("success"):
                    duration = frame.get("duration", 3.0)
                    f.write(f"file '{image['image_path']}'
")
                    f.write(f"duration {duration}
")

        # Build audio concat
        audio_list_path = Path(output_path).parent / "audio_list.txt"
        with open(audio_list_path, "w") as f:
            for seg in audio_segments:
                if seg.get("success"):
                    f.write(f"file '{seg['audio_path']}'
")

        # Resolution mapping
        res_map = {
            "480p": "854x480",
            "720p": "1280x720",
            "1080p": "1920x1080",
            "1440p": "2560x1440",
            "4k": "3840x2160"
        }
        target_res = res_map.get(resolution, "1920x1080")

        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", str(image_list_path),
        ]

        # Add audio if available
        if audio_segments:
            cmd.extend([
                "-f", "concat",
                "-safe", "0",
                "-i", str(audio_list_path)
            ])

        # Video encoding settings
        cmd.extend([
            "-vf", f"scale={target_res.replace('x', ':')},format=yuv420p",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-r", str(fps),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"
        ])

        # Audio encoding
        if audio_segments:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000"
            ])
        else:
            cmd.extend(["-an"])

        cmd.append(output_path)

        # Execute FFmpeg
        logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

        logger.info(f"Video composed: {output_path}")

    async def _fix_video(self, input_path: str, output_path: str, config: Dict):
        """Fix video quality issues"""
        quality_threshold = config.get("quality_threshold", 0.8)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-vf", "unsharp=3:3:1.5,eq=contrast=1.1:brightness=0.05",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-c:a", "copy",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg fix failed: {stderr.decode()}")

    async def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe"""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return json.loads(stdout.decode())
        return {}

    async def add_subtitles(self, video_path: str, subtitle_path: str, output_path: str):
        """Add subtitles to video"""
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vf", f"subtitles={subtitle_path}",
            "-c:a", "copy",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

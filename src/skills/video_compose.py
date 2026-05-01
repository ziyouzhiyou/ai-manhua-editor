"""
Video Composition Utilities
Helper functions for FFmpeg-based video operations
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoComposer:
    """
    Advanced video composition utilities
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    async def create_slideshow(self,
                                images: List[str],
                                durations: List[float],
                                output_path: str,
                                resolution: str = "1920x1080",
                                transition: str = "fade",
                                transition_duration: float = 0.5) -> str:
        """
        Create video slideshow from images

        Args:
            images: List of image paths
            durations: Duration for each image
            output_path: Output video path
            resolution: Output resolution
            transition: Transition type
            transition_duration: Transition duration in seconds
        """
        if len(images) != len(durations):
            raise ValueError("Images and durations must have same length")

        # Build filter complex for transitions
        filter_parts = []
        inputs = []

        for i, (img, dur) in enumerate(zip(images, durations)):
            inputs.extend(["-loop", "1", "-t", str(dur + transition_duration), "-i", img])

        # Build complex filter
        # This is a simplified version - full implementation would handle all transitions
        filter_complex = self._build_transition_filter(len(images), transition, transition_duration)

        cmd = [
            self.ffmpeg_path,
            "-y"
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-s", resolution,
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Slideshow creation failed: {stderr.decode()}")

        return output_path

    def _build_transition_filter(self, count: int, transition: str, duration: float) -> str:
        """Build FFmpeg filter complex for transitions"""
        # Simplified fade transition
        filters = []

        for i in range(count):
            if i == 0:
                filters.append(f"[{i}:v]fade=t=out:st={3-duration}:d={duration}[v{i}]")
            elif i == count - 1:
                filters.append(f"[{i}:v]fade=t=in:st=0:d={duration}[v{i}]")
            else:
                filters.append(f"[{i}:v]fade=t=in:st=0:d={duration},fade=t=out:st={3-duration}:d={duration}[v{i}]")

        # Concatenate
        concat = ";".join(filters)
        concat += ";" + "".join(f"[v{i}]" for i in range(count))
        concat += f"concat=n={count}:v=1:a=0[outv]"

        return concat

    async def add_audio_track(self,
                               video_path: str,
                               audio_path: str,
                               output_path: str,
                               audio_offset: float = 0.0,
                               volume: float = 1.0) -> str:
        """
        Add audio track to video

        Args:
            video_path: Input video
            audio_path: Audio file
            output_path: Output path
            audio_offset: Audio start offset
            volume: Audio volume
        """
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[1:a]adelay={int(audio_offset*1000)}|{int(audio_offset*1000)},volume={volume}[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Audio addition failed: {stderr.decode()}")

        return output_path

    async def burn_subtitles(self,
                              video_path: str,
                              subtitle_path: str,
                              output_path: str,
                              font_size: int = 24,
                              font_color: str = "white",
                              outline_color: str = "black") -> str:
        """
        Burn subtitles into video

        Args:
            video_path: Input video
            subtitle_path: Subtitle file (ASS or SRT)
            output_path: Output path
            font_size: Subtitle font size
            font_color: Font color
            outline_color: Outline color
        """
        # Use ASS if available for styling, otherwise use SRT with basic styling
        if subtitle_path.endswith(".ass"):
            vf = f"subtitles={subtitle_path}"
        else:
            vf = f"subtitles={subtitle_path}:force_style='FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000'"

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vf", vf,
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
            raise RuntimeError(f"Subtitle burning failed: {stderr.decode()}")

        return output_path

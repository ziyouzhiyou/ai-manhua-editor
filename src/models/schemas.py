"""
Data models and schemas for AI Manhua Editor
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SceneType(Enum):
    DIALOGUE = "dialogue"
    ACTION = "action"
    NARRATION = "narration"
    TRANSITION = "transition"
    EMOTION = "emotion"
    FLASHBACK = "flashback"


class CharacterGender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class ImageStyle(Enum):
    ANIME = "anime"
    CINEMATIC_ANIME = "cinematic_anime"
    MANHUA = "manhua"
    CHIBI = "chibi"
    REALISTIC = "realistic"
    WATERCOLOR = "watercolor"


class VoiceEmotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    SCARED = "scared"
    ROMANTIC = "romantic"


@dataclass
class Character:
    """Character definition"""
    id: str
    name: str
    gender: CharacterGender = CharacterGender.UNKNOWN
    age: Optional[int] = None
    description: str = ""
    personality: str = ""
    appearance: str = ""
    voice_id: Optional[str] = None
    reference_images: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender.value,
            "age": self.age,
            "description": self.description,
            "personality": self.personality,
            "appearance": self.appearance,
            "voice_id": self.voice_id,
            "reference_images": self.reference_images,
            "tags": self.tags
        }


@dataclass
class Dialogue:
    """Dialogue line"""
    character_id: str
    text: str
    emotion: VoiceEmotion = VoiceEmotion.NEUTRAL
    speed: float = 1.0
    pause_before: float = 0.0
    pause_after: float = 0.5

    def to_dict(self) -> Dict:
        return {
            "character_id": self.character_id,
            "text": self.text,
            "emotion": self.emotion.value,
            "speed": self.speed,
            "pause_before": self.pause_before,
            "pause_after": self.pause_after
        }


@dataclass
class Scene:
    """Scene definition in a script"""
    id: str
    scene_number: int
    scene_type: SceneType
    title: str = ""
    description: str = ""
    setting: str = ""
    time_of_day: str = ""
    mood: str = ""
    characters: List[str] = field(default_factory=list)
    dialogues: List[Dialogue] = field(default_factory=list)
    action_description: str = ""
    camera_direction: str = ""
    lighting: str = ""
    duration_estimate: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "scene_number": self.scene_number,
            "scene_type": self.scene_type.value,
            "title": self.title,
            "description": self.description,
            "setting": self.setting,
            "time_of_day": self.time_of_day,
            "mood": self.mood,
            "characters": self.characters,
            "dialogues": [d.to_dict() for d in self.dialogues],
            "action_description": self.action_description,
            "camera_direction": self.camera_direction,
            "lighting": self.lighting,
            "duration_estimate": self.duration_estimate
        }


@dataclass
class StoryboardFrame:
    """Individual storyboard frame"""
    id: str
    scene_id: str
    frame_number: int
    description: str = ""
    image_prompt: str = ""
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    camera_angle: str = ""
    camera_movement: str = ""
    duration: float = 3.0
    transition_type: str = "cut"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "scene_id": self.scene_id,
            "frame_number": self.frame_number,
            "description": self.description,
            "image_prompt": self.image_prompt,
            "image_url": self.image_url,
            "image_path": self.image_path,
            "camera_angle": self.camera_angle,
            "camera_movement": self.camera_movement,
            "duration": self.duration,
            "transition_type": self.transition_type
        }


@dataclass
class Storyboard:
    """Complete storyboard for a project"""
    id: str
    project_id: str
    frames: List[StoryboardFrame] = field(default_factory=list)
    style: ImageStyle = ImageStyle.ANIME
    color_palette: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "frames": [f.to_dict() for f in self.frames],
            "style": self.style.value,
            "color_palette": self.color_palette,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class AudioSegment:
    """Audio segment for voice synthesis"""
    id: str
    dialogue_id: str
    character_id: str
    text: str
    audio_path: Optional[str] = None
    duration: float = 0.0
    emotion: VoiceEmotion = VoiceEmotion.NEUTRAL
    start_time: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "dialogue_id": self.dialogue_id,
            "character_id": self.character_id,
            "text": self.text,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "emotion": self.emotion.value,
            "start_time": self.start_time
        }


@dataclass
class SubtitleEntry:
    """Subtitle entry"""
    id: str
    text: str
    start_time: float
    end_time: float
    style: Dict[str, Any] = field(default_factory=dict)
    position: str = "bottom"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "style": self.style,
            "position": self.position
        }


@dataclass
class VideoProject:
    """Complete video project"""
    id: str
    title: str = ""
    description: str = ""
    script_text: str = ""
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    storyboard: Optional[Storyboard] = None
    audio_segments: List[AudioSegment] = field(default_factory=list)
    subtitle_entries: List[SubtitleEntry] = field(default_factory=list)
    output_video_path: Optional[str] = None
    status: str = "created"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "script_text": self.script_text[:500] + "..." if len(self.script_text) > 500 else self.script_text,
            "characters": [c.to_dict() for c in self.characters],
            "scenes": [s.to_dict() for s in self.scenes],
            "storyboard": self.storyboard.to_dict() if self.storyboard else None,
            "audio_segments_count": len(self.audio_segments),
            "subtitle_entries_count": len(self.subtitle_entries),
            "output_video_path": self.output_video_path,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class QualityReport:
    """Quality assessment report"""
    project_id: str
    overall_score: float = 0.0
    image_quality_score: float = 0.0
    audio_quality_score: float = 0.0
    video_quality_score: float = 0.0
    subtitle_quality_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    passed: bool = False

    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "overall_score": self.overall_score,
            "image_quality_score": self.image_quality_score,
            "audio_quality_score": self.audio_quality_score,
            "video_quality_score": self.video_quality_score,
            "subtitle_quality_score": self.subtitle_quality_score,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "passed": self.passed
        }

"""
Enums and constants for AI Manhua Editor
"""
from enum import Enum, auto


class ProjectStatus(Enum):
    CREATED = "created"
    PARSING = "parsing"
    STORYBOARDING = "storyboarding"
    GENERATING_IMAGES = "generating_images"
    SYNTHESIZING_AUDIO = "synthesizing_audio"
    COMPOSING_VIDEO = "composing_video"
    GENERATING_SUBTITLES = "generating_subtitles"
    QUALITY_CHECKING = "quality_checking"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(Enum):
    MP4 = "mp4"
    MKV = "mkv"
    MOV = "mov"
    WEBM = "webm"
    GIF = "gif"


class Resolution(Enum):
    SD_480P = "854x480"
    HD_720P = "1280x720"
    FHD_1080P = "1920x1080"
    QHD_1440P = "2560x1440"
    UHD_4K = "3840x2160"


class TransitionType(Enum):
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    SLIDE = "slide"
    ZOOM = "zoom"
    BLUR = "blur"


class CameraAngle(Enum):
    EYE_LEVEL = "eye_level"
    LOW_ANGLE = "low_angle"
    HIGH_ANGLE = "high_angle"
    DUTCH_ANGLE = "dutch_angle"
    OVERHEAD = "overhead"
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    LONG_SHOT = "long_shot"
    EXTREME_CLOSE_UP = "extreme_close_up"


class LightingStyle(Enum):
    NATURAL = "natural"
    DRAMATIC = "dramatic"
    SOFT = "soft"
    HARD = "hard"
    BACKLIT = "backlit"
    SILHOUETTE = "silhouette"
    NEON = "neon"
    CANDLELIGHT = "candlelight"


class AudioEffect(Enum):
    REVERB = "reverb"
    ECHO = "echo"
    DISTORTION = "distortion"
    PITCH_SHIFT = "pitch_shift"
    SPEED_CHANGE = "speed_change"
    NOISE_REDUCTION = "noise_reduction"


class SubtitleStyle(Enum):
    SIMPLE = "simple"
    ANIME = "anime"
    CINEMATIC = "cinematic"
    COMIC = "comic"
    MINIMAL = "minimal"


class ErrorCode(Enum):
    SUCCESS = 0
    INVALID_INPUT = 1001
    SCRIPT_PARSE_ERROR = 2001
    STORYBOARD_ERROR = 2002
    IMAGE_GENERATION_ERROR = 2003
    TTS_ERROR = 2004
    VIDEO_COMPOSE_ERROR = 2005
    SUBTITLE_ERROR = 2006
    QUALITY_CHECK_FAILED = 2007
    API_ERROR = 3001
    TIMEOUT_ERROR = 3002
    STORAGE_ERROR = 4001
    CONFIG_ERROR = 5001
    UNKNOWN_ERROR = 9999

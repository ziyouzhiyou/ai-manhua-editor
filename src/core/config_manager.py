"""
Configuration Manager for AI Manhua Editor
Supports YAML/JSON configs with environment variable substitution
"""
import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """Application configuration container"""
    # API Keys
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.mimo.ai/v1"

    # Image Generation
    image_provider: str = "mimo"  # mimo, stability, midjourney
    image_model: str = "mimo-image-v2"
    image_quality: str = "high"
    image_size: str = "1024x1024"

    # TTS Configuration
    tts_provider: str = "mimo"  # mimo, azure, elevenlabs
    tts_model: str = "mimo-tts-v1"
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_speed: float = 1.0

    # Video Settings
    video_resolution: str = "1920x1080"
    video_fps: int = 24
    video_codec: str = "h264"
    video_bitrate: str = "8M"

    # Workflow
    default_workflow: str = "standard"
    max_concurrent_tasks: int = 5
    task_timeout: int = 300

    # Storage
    output_dir: str = "./output"
    temp_dir: str = "./temp"
    asset_cache_dir: str = "./cache"

    # OpenClaw Integration
    openclaw_enabled: bool = True
    openclaw_gateway_url: str = "ws://localhost:18789"
    openclaw_skill_name: str = "ai-manhua-editor"

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Advanced
    enable_gpu: bool = False
    gpu_device: str = "cuda:0"
    memory_limit_gb: float = 8.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            k: v for k, v in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ConfigManager:
    """
    Centralized configuration management with:
    - Environment variable substitution
    - Multi-file config merging
    - Runtime config updates
    - Validation
    """

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self._config: Optional[AppConfig] = None
        self._raw_config: Dict[str, Any] = {}

    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in config values"""
        if isinstance(value, str):
            if value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                default = ""
                if ":-" in env_var:
                    env_var, default = env_var.split(":-", 1)
                return os.getenv(env_var, default)
            return value
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_env_vars(v) for v in value]
        return value

    def load_config(self, env: str = "default") -> AppConfig:
        """Load configuration from files and environment"""
        # Load default config
        default_path = self.config_dir / "default.yaml"
        if default_path.exists():
            with open(default_path, "r", encoding="utf-8") as f:
                self._raw_config = yaml.safe_load(f) or {}

        # Load environment-specific config
        env_path = self.config_dir / f"{env}.yaml"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
                self._raw_config = self._deep_merge(self._raw_config, env_config)

        # Substitute environment variables
        self._raw_config = self._substitute_env_vars(self._raw_config)

        # Override with environment variables prefixed with AIMH_
        for key, value in os.environ.items():
            if key.startswith("AIMH_"):
                config_key = key[5:].lower()
                self._raw_config[config_key] = self._parse_env_value(value)

        self._config = AppConfig.from_dict(self._raw_config)
        return self._config

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Try bool
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        # Try int
        try:
            return int(value)
        except ValueError:
            pass
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        if self._config is None:
            self.load_config()
        return self._config

    def update_config(self, updates: Dict[str, Any]) -> AppConfig:
        """Update configuration at runtime"""
        self._raw_config = self._deep_merge(self._raw_config, updates)
        self._config = AppConfig.from_dict(self._raw_config)
        return self._config

    def save_config(self, path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = Path(path) if path else self.config_dir / "runtime.yaml"
        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._raw_config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation (e.g., 'video.resolution')"""
        keys = key.split(".")
        value = self._raw_config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

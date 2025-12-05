"""
Configuration management for AI Ken Burns.

Handles default settings, environment variables, and configuration file loading.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class VideoConfig:
    """Video output configuration."""

    fps: int = 30
    resolution: tuple[int, int] = (1920, 1080)
    output_format: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    pixel_format: str = "yuv420p"

    @property
    def width(self) -> int:
        return self.resolution[0]

    @property
    def height(self) -> int:
        return self.resolution[1]


@dataclass
class KenBurnsConfig:
    """Ken Burns effect configuration."""

    intensity: float = 0.5  # 0.0 = minimal motion, 1.0 = maximum motion
    min_scale: float = 1.0
    max_scale: float = 1.5
    default_segment_duration: float = 5.0  # seconds


@dataclass
class LLMConfig:
    """LLM provider configuration - uses OpenAI by default."""

    provider: str = "openai"

    # Model selection for different tasks
    research_model: str = "gpt-4o"  # For historical analysis (needs reasoning)
    generation_model: str = "gpt-4o"  # For script generation

    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    temperature: float = 0.7
    max_retries: int = 3
    request_timeout: int = 60  # seconds

    # Rate limiting
    retry_delay_base: float = 1.0  # Base delay for exponential backoff
    retry_delay_max: float = 30.0  # Maximum delay between retries


@dataclass
class TTSConfig:
    """Text-to-speech configuration."""

    model: str = "tts-1-hd"  # High quality TTS
    voice: str = "onyx"  # Deep, authoritative voice
    speed: float = 1.0
    response_format: str = "wav"


@dataclass
class ResearchConfig:
    """Research pipeline configuration."""

    # Google News RSS settings
    news_rss_url: str = "https://news.google.com/rss"
    news_topics: list[str] = field(default_factory=lambda: [
        "business", "economy", "politics"
    ])

    # Relevance keywords for filtering news
    relevance_keywords: list[str] = field(default_factory=lambda: [
        "labor", "union", "strike", "workers", "wage",
        "layoff", "unemployment", "economy", "inequality",
        "protest", "activism", "corporate", "billionaire",
        "housing", "healthcare", "minimum wage"
    ])

    # Historical connection settings
    min_historical_year: int = 1800  # Don't go earlier than this
    preferred_era_start: int = 1870  # Prefer labor movement era
    confidence_threshold: float = 0.7  # Minimum confidence for connections


@dataclass
class PathConfig:
    """Path configuration for project directories."""

    base_dir: Path = field(default_factory=lambda: Path.cwd())

    @property
    def artifacts_dir(self) -> Path:
        return self.base_dir / "artifacts"

    @property
    def images_dir(self) -> Path:
        return self.artifacts_dir / "images"

    @property
    def placeholders_dir(self) -> Path:
        return self.artifacts_dir / "placeholders"

    @property
    def temp_dir(self) -> Path:
        return self.artifacts_dir / "temp"

    @property
    def drafts_dir(self) -> Path:
        return self.artifacts_dir / "drafts"

    @property
    def output_dir(self) -> Path:
        return self.base_dir / "output"

    # Research pipeline artifacts
    @property
    def research_dir(self) -> Path:
        return self.artifacts_dir / "research"

    @property
    def scripts_dir(self) -> Path:
        return self.artifacts_dir / "scripts"

    @property
    def audio_dir(self) -> Path:
        return self.artifacts_dir / "audio"

    def ensure_dirs(self) -> None:
        """Create all required directories."""
        for dir_path in [
            self.artifacts_dir,
            self.images_dir,
            self.placeholders_dir,
            self.temp_dir,
            self.drafts_dir,
            self.output_dir,
            self.research_dir,
            self.scripts_dir,
            self.audio_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Main application configuration."""

    video: VideoConfig = field(default_factory=VideoConfig)
    ken_burns: KenBurnsConfig = field(default_factory=KenBurnsConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Feature flags
    save_artifacts: bool = True  # Save intermediate JSON files

    def __post_init__(self) -> None:
        """Initialize paths after creation."""
        self.paths.ensure_dirs()

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.llm.api_key:
            errors.append(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )

        if self.video.fps < 1 or self.video.fps > 120:
            errors.append(f"Invalid FPS: {self.video.fps}. Must be 1-120.")

        if self.ken_burns.intensity < 0 or self.ken_burns.intensity > 1:
            errors.append(
                f"Invalid Ken Burns intensity: {self.ken_burns.intensity}. Must be 0-1."
            )

        return errors


# Global default configuration
_default_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global application configuration."""
    global _default_config
    if _default_config is None:
        _default_config = AppConfig()
    return _default_config


def set_config(config: AppConfig) -> None:
    """Set the global application configuration."""
    global _default_config
    _default_config = config


def validate_config() -> None:
    """Validate configuration and raise if invalid."""
    config = get_config()
    errors = config.validate()
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


def parse_resolution(resolution_str: str) -> tuple[int, int]:
    """Parse resolution string like '1920x1080' into tuple."""
    try:
        parts = resolution_str.lower().split("x")
        if len(parts) != 2:
            raise ValueError(f"Invalid resolution format: {resolution_str}")
        width, height = int(parts[0]), int(parts[1])
        if width <= 0 or height <= 0:
            raise ValueError(f"Resolution must be positive: {resolution_str}")
        return (width, height)
    except ValueError as e:
        raise ValueError(f"Invalid resolution '{resolution_str}': {e}")

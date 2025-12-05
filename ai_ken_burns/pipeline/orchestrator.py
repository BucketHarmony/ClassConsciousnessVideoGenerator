"""
Pipeline orchestrator for AI Ken Burns.

Provides centralized pipeline management with:
- Stage-by-stage execution
- Progress tracking
- Error recovery
- Artifact management
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from ai_ken_burns.config import get_config
from ai_ken_burns.pipeline.errors import (
    PipelineError,
    StageError,
    RecoveryStrategy,
    api_error,
    validation_error,
)
from ai_ken_burns.utils.logging_utils import (
    get_logger,
    log_timing,
    PipelineProgress,
    print_info,
    print_success,
    print_error,
    print_warning,
)

logger = get_logger("ai_ken_burns.pipeline")


class PipelineStage(str, Enum):
    """Pipeline stages in execution order."""

    RESEARCH = "research"
    SCRIPT = "script"
    AUDIO = "audio"
    IMAGES = "images"
    MOTION = "motion"
    RENDER = "render"


@dataclass
class StageResult:
    """Result from a single pipeline stage."""

    stage: PipelineStage
    success: bool
    data: Any = None
    error: Optional[StageError] = None
    duration_seconds: float = 0.0
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""

    success: bool
    output_path: Optional[str] = None
    stage_results: list[StageResult] = field(default_factory=list)
    total_duration: float = 0.0
    errors: list[StageError] = field(default_factory=list)

    @property
    def failed_stage(self) -> Optional[PipelineStage]:
        """Get the stage where pipeline failed, if any."""
        for result in self.stage_results:
            if not result.success:
                return result.stage
        return None

    @property
    def all_artifacts(self) -> dict[str, str]:
        """Get all artifacts from all stages."""
        artifacts = {}
        for result in self.stage_results:
            artifacts.update(result.artifacts)
        return artifacts


class Pipeline:
    """
    Orchestrates the full video generation pipeline.

    Manages stage execution, progress tracking, and error recovery.
    """

    def __init__(
        self,
        topic: Optional[str] = None,
        style: str = "documentary style, thoughtful and engaging",
        target_duration: int = 90,
        images_dir: Optional[Path] = None,
        output_path: Optional[Path] = None,
        ken_burns_intensity: float = 0.5,
        save_artifacts: bool = True,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            topic: News topic filter
            style: Narrative style
            target_duration: Target video duration in seconds
            images_dir: Optional local images directory
            output_path: Output video path
            ken_burns_intensity: Motion intensity (0-1)
            save_artifacts: Whether to save intermediate files
        """
        self.config = get_config()
        self.topic = topic
        self.style = style
        self.target_duration = target_duration
        self.images_dir = images_dir
        self.output_path = output_path or self._default_output_path()
        self.ken_burns_intensity = ken_burns_intensity
        self.save_artifacts = save_artifacts

        # Pipeline state
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.artifacts_dir = self.config.paths.artifacts_dir / self.timestamp
        self.stage_data: dict[PipelineStage, Any] = {}
        self.stage_results: list[StageResult] = []

        # Progress callback
        self.on_progress: Optional[Callable[[PipelineStage, float], None]] = None

    def _default_output_path(self) -> Path:
        """Generate default output path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.config.paths.output_dir / f"class_consciousness_{timestamp}.mp4"

    def run(self) -> PipelineResult:
        """
        Execute the complete pipeline.

        Returns:
            PipelineResult with success status and artifacts
        """
        logger.info("Starting pipeline execution")
        start_time = time.perf_counter()

        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        stages = [
            (PipelineStage.RESEARCH, self._run_research),
            (PipelineStage.SCRIPT, self._run_script),
            (PipelineStage.AUDIO, self._run_audio),
            (PipelineStage.IMAGES, self._run_images),
            (PipelineStage.MOTION, self._run_motion),
            (PipelineStage.RENDER, self._run_render),
        ]

        for stage, stage_func in stages:
            result = self._execute_stage(stage, stage_func)
            self.stage_results.append(result)

            if not result.success:
                logger.error(f"Pipeline failed at stage: {stage.value}")
                return PipelineResult(
                    success=False,
                    stage_results=self.stage_results,
                    total_duration=time.perf_counter() - start_time,
                    errors=[r.error for r in self.stage_results if r.error],
                )

        total_duration = time.perf_counter() - start_time
        logger.info(f"Pipeline completed successfully in {total_duration:.1f}s")

        return PipelineResult(
            success=True,
            output_path=str(self.output_path),
            stage_results=self.stage_results,
            total_duration=total_duration,
        )

    def _execute_stage(
        self,
        stage: PipelineStage,
        stage_func: Callable[[], Any],
    ) -> StageResult:
        """Execute a single stage with error handling."""
        logger.info(f"Executing stage: {stage.value}")
        start_time = time.perf_counter()

        try:
            with log_timing(f"stage_{stage.value}", logger):
                data = stage_func()

            self.stage_data[stage] = data
            duration = time.perf_counter() - start_time

            # Save artifacts if enabled
            artifacts = {}
            if self.save_artifacts:
                artifacts = self._save_stage_artifacts(stage, data)

            return StageResult(
                stage=stage,
                success=True,
                data=data,
                duration_seconds=duration,
                artifacts=artifacts,
            )

        except PipelineError as e:
            duration = time.perf_counter() - start_time
            logger.error(f"Stage {stage.value} failed: {e}")

            return StageResult(
                stage=stage,
                success=False,
                error=e.stage_error,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(f"Unexpected error in stage {stage.value}: {e}")

            error = StageError(
                stage=stage.value,
                message=str(e),
                error_type="unexpected_error",
                recovery_strategy=RecoveryStrategy.ABORT,
            )

            return StageResult(
                stage=stage,
                success=False,
                error=error,
                duration_seconds=duration,
            )

    def _save_stage_artifacts(self, stage: PipelineStage, data: Any) -> dict[str, str]:
        """Save stage artifacts to disk."""
        artifacts = {}

        try:
            if stage == PipelineStage.RESEARCH:
                path = self.artifacts_dir / "research.json"
                path.write_text(data.model_dump_json(indent=2))
                artifacts["research"] = str(path)

            elif stage == PipelineStage.SCRIPT:
                path = self.artifacts_dir / "script.json"
                path.write_text(data.model_dump_json(indent=2))
                artifacts["script"] = str(path)

            elif stage == PipelineStage.AUDIO:
                path = self.artifacts_dir / "audio_metadata.json"
                path.write_text(data.model_dump_json(indent=2))
                artifacts["audio_metadata"] = str(path)

            elif stage == PipelineStage.IMAGES:
                path = self.artifacts_dir / "images.json"
                path.write_text(data.model_dump_json(indent=2))
                artifacts["images"] = str(path)

            elif stage == PipelineStage.MOTION:
                path = self.artifacts_dir / "render_spec.json"
                path.write_text(data.model_dump_json(indent=2))
                artifacts["render_spec"] = str(path)

        except Exception as e:
            logger.warning(f"Failed to save artifacts for {stage.value}: {e}")

        return artifacts

    def _run_research(self) -> Any:
        """Execute research stage."""
        from ai_ken_burns.research.news_fetcher import NewsFetcher
        from ai_ken_burns.research.historical_connector import HistoricalConnector

        # Fetch news
        fetcher = NewsFetcher()
        stories = fetcher.get_top_stories(topic=self.topic, max_stories=5)

        if not stories:
            raise PipelineError(validation_error(
                "research",
                "No relevant news stories found",
                {"topic": self.topic},
            ))

        # Find historical connection
        connector = HistoricalConnector()
        research = connector.find_best_connection(stories, topic=self.topic)

        if not research:
            raise PipelineError(api_error(
                "research",
                "Failed to find historical connection",
            ))

        return research

    def _run_script(self) -> Any:
        """Execute script generation stage."""
        from ai_ken_burns.script.generator import ScriptGenerator

        research = self.stage_data.get(PipelineStage.RESEARCH)
        if not research:
            raise PipelineError(validation_error(
                "script",
                "Research data not available",
            ))

        generator = ScriptGenerator()
        script = generator.generate(
            research=research,
            style=self.style,
            target_duration=self.target_duration,
        )

        if not script:
            raise PipelineError(api_error(
                "script",
                "Failed to generate script",
            ))

        return script

    def _run_audio(self) -> Any:
        """Execute audio generation stage."""
        from ai_ken_burns.audio.tts_generator import TTSGenerator

        script = self.stage_data.get(PipelineStage.SCRIPT)
        if not script:
            raise PipelineError(validation_error(
                "audio",
                "Script data not available",
            ))

        audio_dir = self.artifacts_dir / "audio"
        generator = TTSGenerator()
        audio = generator.generate(
            script=script,
            output_dir=audio_dir,
            generate_segments=True,
        )

        if not audio:
            raise PipelineError(api_error(
                "audio",
                "Failed to generate audio",
            ))

        return audio

    def _run_images(self) -> Any:
        """Execute image gathering stage."""
        from ai_ken_burns.images.manager import ImageManager

        script = self.stage_data.get(PipelineStage.SCRIPT)
        if not script:
            raise PipelineError(validation_error(
                "images",
                "Script data not available",
            ))

        images_output_dir = self.artifacts_dir / "images"
        manager = ImageManager(images_dir=images_output_dir)

        try:
            if self.images_dir:
                collection = manager.use_local_images(script, self.images_dir)
            else:
                collection = manager.gather_images(script, images_per_marker=3)
        finally:
            manager.close()

        if collection.markers_covered == 0:
            raise PipelineError(validation_error(
                "images",
                "No images found for any markers",
            ))

        return collection

    def _run_motion(self) -> Any:
        """Execute motion parameter generation stage."""
        from ai_ken_burns.video.ken_burns import KenBurnsEngine

        script = self.stage_data.get(PipelineStage.SCRIPT)
        audio = self.stage_data.get(PipelineStage.AUDIO)
        images = self.stage_data.get(PipelineStage.IMAGES)

        if not all([script, audio, images]):
            raise PipelineError(validation_error(
                "motion",
                "Required data not available from previous stages",
            ))

        engine = KenBurnsEngine(intensity=self.ken_burns_intensity)
        render_spec = engine.create_render_spec(
            script, audio, images, str(self.output_path)
        )
        render_spec = engine.add_variety(render_spec)

        return render_spec

    def _run_render(self) -> Any:
        """Execute video rendering stage."""
        from ai_ken_burns.video.renderer import VideoRenderer

        render_spec = self.stage_data.get(PipelineStage.MOTION)
        if not render_spec:
            raise PipelineError(validation_error(
                "render",
                "Render spec not available",
            ))

        renderer = VideoRenderer(temp_dir=self.artifacts_dir / "temp")
        success = renderer.render(render_spec)

        if not success:
            raise PipelineError(StageError(
                stage="render",
                message="Video rendering failed",
                error_type="render_error",
                recovery_strategy=RecoveryStrategy.ABORT,
            ))

        renderer.cleanup_temp_files(render_spec)

        return render_spec

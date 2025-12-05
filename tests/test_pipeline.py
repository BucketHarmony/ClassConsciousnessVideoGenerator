"""
Integration tests for the pipeline orchestrator.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestPipelineErrors:
    """Tests for pipeline error handling."""

    def test_stage_error_creation(self):
        """Test StageError creation."""
        from ai_ken_burns.pipeline.errors import StageError, RecoveryStrategy

        error = StageError(
            stage="test",
            message="Test error",
            error_type="test_error",
            recovery_strategy=RecoveryStrategy.RETRY,
            is_recoverable=True,
        )

        assert error.stage == "test"
        assert error.can_retry

    def test_stage_error_retry_limit(self):
        """Test StageError retry limit."""
        from ai_ken_burns.pipeline.errors import StageError, RecoveryStrategy

        error = StageError(
            stage="test",
            message="Test error",
            recovery_strategy=RecoveryStrategy.RETRY,
            is_recoverable=True,
            retry_count=3,
            max_retries=3,
        )

        assert not error.can_retry

    def test_error_factories(self):
        """Test error factory functions."""
        from ai_ken_burns.pipeline.errors import (
            api_error,
            network_error,
            validation_error,
            RecoveryStrategy,
        )

        api_err = api_error("test", "API failed")
        assert api_err.is_recoverable
        assert api_err.recovery_strategy == RecoveryStrategy.RETRY

        net_err = network_error("test", "Network failed")
        assert net_err.max_retries == 5

        val_err = validation_error("test", "Invalid data")
        assert not val_err.is_recoverable
        assert val_err.recovery_strategy == RecoveryStrategy.ABORT


class TestPipelineOrchestrator:
    """Tests for Pipeline orchestrator."""

    def test_pipeline_initialization(self, temp_dir):
        """Test Pipeline initialization."""
        from ai_ken_burns.pipeline.orchestrator import Pipeline

        pipeline = Pipeline(
            topic="labor",
            style="documentary",
            target_duration=60,
            output_path=temp_dir / "output.mp4",
        )

        assert pipeline.topic == "labor"
        assert pipeline.target_duration == 60

    def test_pipeline_stage_order(self):
        """Test pipeline stages are in correct order."""
        from ai_ken_burns.pipeline.orchestrator import PipelineStage

        stages = list(PipelineStage)
        assert stages[0] == PipelineStage.RESEARCH
        assert stages[-1] == PipelineStage.RENDER

    def test_stage_result_creation(self):
        """Test StageResult creation."""
        from ai_ken_burns.pipeline.orchestrator import StageResult, PipelineStage

        result = StageResult(
            stage=PipelineStage.RESEARCH,
            success=True,
            data={"test": "data"},
            duration_seconds=5.0,
        )

        assert result.success
        assert result.duration_seconds == 5.0

    def test_pipeline_result_properties(self):
        """Test PipelineResult computed properties."""
        from ai_ken_burns.pipeline.orchestrator import (
            PipelineResult,
            StageResult,
            PipelineStage,
        )

        failed_result = StageResult(
            stage=PipelineStage.AUDIO,
            success=False,
        )

        pipeline_result = PipelineResult(
            success=False,
            stage_results=[
                StageResult(stage=PipelineStage.RESEARCH, success=True),
                StageResult(stage=PipelineStage.SCRIPT, success=True),
                failed_result,
            ],
        )

        assert pipeline_result.failed_stage == PipelineStage.AUDIO


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_help(self):
        """Test CLI help command."""
        from typer.testing import CliRunner
        from ai_ken_burns.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "generate" in result.stdout
        assert "research-only" in result.stdout

    def test_cli_info_command(self):
        """Test info command runs."""
        from typer.testing import CliRunner
        from ai_ken_burns.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["info"])

        # Should run without error (exit code 0 is normal)
        assert "System Status" in result.stdout or result.exit_code == 0

    def test_cli_validate_command(self):
        """Test validate command runs."""
        from typer.testing import CliRunner
        from ai_ken_burns.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["validate"])

        # May fail if dependencies not set up, but shouldn't crash
        assert result.exit_code in [0, 1]

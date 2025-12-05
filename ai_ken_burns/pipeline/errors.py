"""
Error handling and recovery for AI Ken Burns pipeline.

Provides structured error types and recovery strategies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RecoveryStrategy(str, Enum):
    """Available recovery strategies for pipeline errors."""

    RETRY = "retry"  # Retry the failed operation
    SKIP = "skip"  # Skip and continue with next stage
    FALLBACK = "fallback"  # Use fallback/default value
    ABORT = "abort"  # Stop pipeline execution


@dataclass
class StageError:
    """
    Error that occurred during a pipeline stage.

    Contains error details and suggested recovery strategy.
    """

    stage: str
    message: str
    error_type: str = "unknown"
    details: dict[str, Any] = field(default_factory=dict)
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.ABORT
    is_recoverable: bool = False
    retry_count: int = 0
    max_retries: int = 3

    @property
    def can_retry(self) -> bool:
        """Check if retry is possible."""
        return (
            self.is_recoverable
            and self.recovery_strategy == RecoveryStrategy.RETRY
            and self.retry_count < self.max_retries
        )

    def increment_retry(self) -> "StageError":
        """Increment retry count and return updated error."""
        self.retry_count += 1
        return self


class PipelineError(Exception):
    """
    Exception raised during pipeline execution.

    Wraps StageError with exception semantics.
    """

    def __init__(self, stage_error: StageError) -> None:
        self.stage_error = stage_error
        super().__init__(f"[{stage_error.stage}] {stage_error.message}")

    @property
    def stage(self) -> str:
        return self.stage_error.stage

    @property
    def is_recoverable(self) -> bool:
        return self.stage_error.is_recoverable

    @property
    def recovery_strategy(self) -> RecoveryStrategy:
        return self.stage_error.recovery_strategy


# Common error factories
def api_error(stage: str, message: str, details: Optional[dict] = None) -> StageError:
    """Create an API-related error (typically retryable)."""
    return StageError(
        stage=stage,
        message=message,
        error_type="api_error",
        details=details or {},
        recovery_strategy=RecoveryStrategy.RETRY,
        is_recoverable=True,
        max_retries=3,
    )


def network_error(stage: str, message: str) -> StageError:
    """Create a network-related error (retryable)."""
    return StageError(
        stage=stage,
        message=message,
        error_type="network_error",
        recovery_strategy=RecoveryStrategy.RETRY,
        is_recoverable=True,
        max_retries=5,
    )


def validation_error(stage: str, message: str, details: Optional[dict] = None) -> StageError:
    """Create a validation error (not retryable)."""
    return StageError(
        stage=stage,
        message=message,
        error_type="validation_error",
        details=details or {},
        recovery_strategy=RecoveryStrategy.ABORT,
        is_recoverable=False,
    )


def resource_error(stage: str, message: str, fallback_available: bool = False) -> StageError:
    """Create a resource-related error (may have fallback)."""
    return StageError(
        stage=stage,
        message=message,
        error_type="resource_error",
        recovery_strategy=RecoveryStrategy.FALLBACK if fallback_available else RecoveryStrategy.ABORT,
        is_recoverable=fallback_available,
    )


def ffmpeg_error(stage: str, message: str, details: Optional[dict] = None) -> StageError:
    """Create an FFmpeg-related error."""
    return StageError(
        stage=stage,
        message=message,
        error_type="ffmpeg_error",
        details=details or {},
        recovery_strategy=RecoveryStrategy.ABORT,
        is_recoverable=False,
    )

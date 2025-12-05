"""
Enhanced logging utilities for AI Ken Burns.

Provides structured logging with Rich console output, component-specific loggers,
and timing metrics for pipeline stages.
"""

from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.panel import Panel
from rich.table import Table

# Rich console for output
console = Console()

# Component loggers registry
_loggers: dict[str, logging.Logger] = {}

# Timing metrics storage
_timing_metrics: dict[str, list[float]] = {}


def get_logger(name: str = "ai_ken_burns") -> logging.Logger:
    """Get or create a named logger with Rich formatting."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.propagate = False

    # Rich handler for console output
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    rich_handler.setLevel(logging.INFO)
    rich_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(rich_handler)
    _loggers[name] = logger

    return logger


# Pre-defined component loggers
def get_research_logger() -> logging.Logger:
    """Logger for research pipeline (news, historical)."""
    return get_logger("ai_ken_burns.research")


def get_script_logger() -> logging.Logger:
    """Logger for script generation."""
    return get_logger("ai_ken_burns.script")


def get_audio_logger() -> logging.Logger:
    """Logger for audio/TTS pipeline."""
    return get_logger("ai_ken_burns.audio")


def get_video_logger() -> logging.Logger:
    """Logger for video rendering pipeline."""
    return get_logger("ai_ken_burns.video")


def get_api_logger() -> logging.Logger:
    """Logger for API calls (OpenAI, etc.)."""
    return get_logger("ai_ken_burns.api")


def set_log_level(level: str, logger_name: Optional[str] = None) -> None:
    """Set the logging level for a specific or all loggers."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    if logger_name:
        if logger_name in _loggers:
            for handler in _loggers[logger_name].handlers:
                handler.setLevel(numeric_level)
    else:
        for logger in _loggers.values():
            for handler in logger.handlers:
                handler.setLevel(numeric_level)


def setup_file_logging(log_dir: Path, log_level: str = "DEBUG") -> None:
    """Add file logging to all component loggers."""
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ai_ken_burns_{timestamp}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    for logger in _loggers.values():
        logger.addHandler(file_handler)


@contextmanager
def log_timing(operation: str, logger: Optional[logging.Logger] = None) -> Generator[None, None, None]:
    """Context manager to log timing of an operation."""
    logger = logger or get_logger()
    start_time = time.perf_counter()

    logger.debug(f"Starting: {operation}")

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time

        # Store metric
        if operation not in _timing_metrics:
            _timing_metrics[operation] = []
        _timing_metrics[operation].append(elapsed)

        logger.info(f"Completed: {operation} ({elapsed:.2f}s)")


def timed(operation_name: Optional[str] = None) -> Callable:
    """Decorator to log timing of a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with log_timing(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_timing_metrics() -> dict[str, dict[str, float]]:
    """Get summary of timing metrics."""
    summary = {}
    for operation, times in _timing_metrics.items():
        summary[operation] = {
            "count": len(times),
            "total": sum(times),
            "avg": sum(times) / len(times) if times else 0,
            "min": min(times) if times else 0,
            "max": max(times) if times else 0,
        }
    return summary


def log_timing_summary(logger: Optional[logging.Logger] = None) -> None:
    """Log a summary of all timing metrics."""
    logger = logger or get_logger()
    metrics = get_timing_metrics()

    if not metrics:
        logger.info("No timing metrics recorded")
        return

    table = Table(title="Timing Metrics Summary")
    table.add_column("Operation", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Total (s)", justify="right")
    table.add_column("Avg (s)", justify="right")
    table.add_column("Min (s)", justify="right")
    table.add_column("Max (s)", justify="right")

    for op, stats in sorted(metrics.items()):
        table.add_row(
            op,
            str(stats["count"]),
            f"{stats['total']:.2f}",
            f"{stats['avg']:.2f}",
            f"{stats['min']:.2f}",
            f"{stats['max']:.2f}",
        )

    console.print(table)


def log_error_context(
    error: Exception,
    context: dict[str, Any],
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log an error with full context for debugging."""
    logger = logger or get_logger()

    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
    }

    logger.error(f"Error occurred: {error}")
    logger.debug(f"Error context: {error_info}")


def create_progress() -> Progress:
    """Create a rich progress bar for pipeline operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


class PipelineProgress:
    """Context manager for tracking pipeline progress with multiple stages."""

    STAGES = [
        ("research", "Researching news..."),
        ("historical", "Finding historical connection..."),
        ("script", "Generating script..."),
        ("tts", "Creating audio..."),
        ("images", "Gathering images..."),
        ("render", "Rendering video..."),
    ]

    def __init__(self, stages: Optional[list[tuple[str, str]]] = None) -> None:
        self.stages = stages or self.STAGES
        self.progress: Optional[Progress] = None
        self.task_ids: dict[str, int] = {}
        self.current_stage: Optional[str] = None

    def __enter__(self) -> "PipelineProgress":
        self.progress = create_progress()
        self.progress.start()

        for stage_id, description in self.stages:
            task_id = self.progress.add_task(description, total=100, visible=False)
            self.task_ids[stage_id] = task_id

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.progress:
            self.progress.stop()

    def start_stage(self, stage_id: str) -> None:
        """Start a pipeline stage."""
        if self.progress and stage_id in self.task_ids:
            # Hide previous stage
            if self.current_stage and self.current_stage in self.task_ids:
                self.progress.update(self.task_ids[self.current_stage], visible=False)

            self.current_stage = stage_id
            self.progress.update(self.task_ids[stage_id], visible=True, completed=0)

    def update_stage(self, stage_id: str, progress: float) -> None:
        """Update progress of a stage (0-100)."""
        if self.progress and stage_id in self.task_ids:
            self.progress.update(self.task_ids[stage_id], completed=progress)

    def complete_stage(self, stage_id: str) -> None:
        """Mark a stage as complete."""
        if self.progress and stage_id in self.task_ids:
            self.progress.update(self.task_ids[stage_id], completed=100)


def print_banner() -> None:
    """Print application banner."""
    banner = """
+-----------------------------------------------------------+
|     Class Consciousness Video Generator                   |
|     Connecting Today's News to Historical Struggles       |
+-----------------------------------------------------------+
    """
    console.print(Panel(banner, style="bold blue"))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green][OK][/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red][ERROR][/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow][WARN][/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue][INFO][/bold blue] {message}")

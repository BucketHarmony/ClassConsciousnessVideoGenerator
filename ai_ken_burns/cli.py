"""
Command-line interface for AI Ken Burns Class Consciousness Video Generator.

Provides commands for:
- Full pipeline: news -> research -> script -> audio -> video
- Sub-stages: research-only, script-only, etc.
- Configuration and status
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_ken_burns import __version__
from ai_ken_burns.config import (
    AppConfig,
    get_config,
    parse_resolution,
    set_config,
    validate_config,
)
from ai_ken_burns.utils.logging_utils import (
    get_logger,
    set_log_level,
    print_banner,
    print_success,
    print_error,
    print_info,
    print_warning,
    PipelineProgress,
    log_timing_summary,
)

# Typer application
app = typer.Typer(
    name="ai-ken-burns",
    help="Class Consciousness Video Generator - Connect today's news to historical struggles",
    add_completion=False,
)

console = Console()
logger = get_logger()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"ai-ken-burns version {__version__}")
        raise typer.Exit()


@app.command()
def generate(
    # Optional topic filter
    topic: Optional[str] = typer.Option(
        None,
        "--topic",
        "-t",
        help="Topic to filter news (e.g., 'labor', 'economy', 'housing')",
    ),
    # Style prompt
    style: str = typer.Option(
        "documentary style, thoughtful and engaging",
        "--style",
        "-s",
        help="Style prompt for the narrative",
    ),
    # Image options
    images_dir: Optional[Path] = typer.Option(
        None,
        "--images-dir",
        "-i",
        exists=True,
        file_okay=False,
        help="Directory containing images to use in the video",
    ),
    # Output options
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output video file path (default: output/YYYYMMDD_HHMMSS.mp4)",
    ),
    # Video options
    resolution: str = typer.Option(
        "square",
        "--resolution",
        "-r",
        help="Video resolution: preset (tiktok, reels, 1080p, 4k, square) or WxH",
    ),
    fps: int = typer.Option(
        30,
        "--fps",
        min=1,
        max=120,
        help="Frames per second",
    ),
    ken_burns_intensity: float = typer.Option(
        0.5,
        "--ken-burns-intensity",
        "-k",
        min=0.0,
        max=1.0,
        help="Ken Burns effect intensity (0.0 = minimal, 1.0 = maximum)",
    ),
    min_relevance: float = typer.Option(
        0.0,
        "--min-relevance",
        min=0.0,
        max=1.0,
        help="Minimum relevance score for news stories (0-1)",
    ),
    # AI Image generation options
    ai_images: bool = typer.Option(
        True,
        "--ai-images/--no-ai-images",
        help="Use DALL-E to generate images when search fails",
    ),
    ai_images_only: bool = typer.Option(
        False,
        "--ai-images-only",
        help="Use only AI-generated images (skip image search)",
    ),
    # Artifact options
    save_artifacts: bool = typer.Option(
        True,
        "--save-artifacts/--no-save-artifacts",
        help="Save intermediate JSON files for debugging",
    ),
    # Publishing options
    publish: bool = typer.Option(
        False,
        "--publish",
        "-p",
        help="Publish video to TikTok after generation",
    ),
    publish_headless: bool = typer.Option(
        True,
        "--publish-headless/--publish-visible",
        help="Run browser in headless mode for publishing",
    ),
    # Logging
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    Generate a complete Class Consciousness video.

    Full pipeline: news research -> historical connection -> script -> audio -> video

    Examples:

        ai-ken-burns generate

        ai-ken-burns generate --topic labor --style "urgent documentary"

        ai-ken-burns generate --images-dir ./photos --output my_video.mp4
    """
    print_banner()

    # Set up logging
    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    config = get_config()
    config.save_artifacts = save_artifacts

    # Parse resolution (supports presets like 'tiktok' or WxH format)
    from ai_ken_burns.config import get_resolution
    try:
        video_resolution = get_resolution(resolution)
        config.video.resolution = video_resolution
        config.video.fps = fps
        config.ken_burns.intensity = ken_burns_intensity
    except ValueError as e:
        print_error(f"Invalid resolution: {e}")
        raise typer.Exit(1)

    # Determine if vertical (for DALL-E image size)
    is_vertical = video_resolution[1] > video_resolution[0]

    # Set default output path
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = config.paths.output_dir / f"class_consciousness_{timestamp}.mp4"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    print_info(f"Output: {output}")
    print_info(f"Resolution: {video_resolution[0]}x{video_resolution[1]} @ {fps}fps")
    if topic:
        print_info(f"Topic filter: {topic}")

    # Import pipeline components
    from ai_ken_burns.research.news_fetcher import NewsFetcher
    from ai_ken_burns.research.historical_connector import HistoricalConnector
    from ai_ken_burns.script.generator import ScriptGenerator
    from ai_ken_burns.audio.tts_generator import TTSGenerator
    from ai_ken_burns.images.manager import ImageManager
    from ai_ken_burns.video.ken_burns import KenBurnsEngine
    from ai_ken_burns.video.renderer import VideoRenderer

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Stage 1: Research
    print_info("\n[Stage 1/6] Fetching news and finding historical connection...")
    fetcher = NewsFetcher()
    stories = fetcher.get_top_stories(topic=topic, max_stories=5, min_relevance=min_relevance)

    if not stories:
        print_error("No relevant news stories found")
        raise typer.Exit(1)

    print_success(f"Found {len(stories)} relevant stories")

    connector = HistoricalConnector()
    research = connector.find_best_connection(stories, topic=topic)

    if not research:
        print_error("Failed to find historical connection")
        raise typer.Exit(1)

    print_success(f"Connected to: {research.historical_event.name}")

    if save_artifacts:
        research_path = config.paths.research_dir / f"research_{timestamp}.json"
        research_path.parent.mkdir(parents=True, exist_ok=True)
        research_path.write_text(research.model_dump_json(indent=2))

    # Stage 2: Script
    print_info("\n[Stage 2/6] Generating script...")
    generator = ScriptGenerator()
    script = generator.generate(research=research, style=style, target_duration=90)

    if not script:
        print_error("Failed to generate script")
        raise typer.Exit(1)

    print_success(f"Generated script: {script.segment_count} segments, {script.marker_count} markers")

    if save_artifacts:
        script_path = config.paths.scripts_dir / f"script_{timestamp}.json"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(script.model_dump_json(indent=2))

        # Also save script next to output video for convenience
        output_script_path = output.parent / f"{output.stem}_script.json"
        output_script_path.write_text(script.model_dump_json(indent=2))

    # Stage 3: Audio
    print_info("\n[Stage 3/6] Generating audio...")
    audio_dir = config.paths.audio_dir / f"audio_{timestamp}"
    tts = TTSGenerator()
    audio = tts.generate(script=script, output_dir=audio_dir, generate_segments=True)

    if not audio:
        print_error("Failed to generate audio")
        raise typer.Exit(1)

    print_success(f"Generated audio: {audio.total_duration:.1f}s")

    if save_artifacts:
        metadata_path = audio_dir / "audio_metadata.json"
        metadata_path.write_text(audio.model_dump_json(indent=2))

    # Stage 4: Images
    print_info("\n[Stage 4/6] Gathering images...")
    img_manager = ImageManager(
        use_ai_generation=ai_images,
        ai_generation_only=ai_images_only,
        is_vertical=is_vertical,
    )

    # Build historical context for AI generation
    historical_context = f"{research.historical_event.name}. {research.thesis}"

    if images_dir:
        # Use provided local images
        images = img_manager.use_local_images(script, images_dir)
    else:
        # Search for images online (with AI fallback if enabled)
        images = img_manager.gather_images(
            script,
            images_per_marker=3,
            historical_context=historical_context,
        )

    img_manager.close()

    if images.markers_covered == 0:
        print_error("No images found for any markers")
        raise typer.Exit(1)

    ai_count = images.ai_generated_count
    search_count = images.downloaded_count - ai_count
    if ai_count > 0:
        print_success(f"Gathered {search_count} searched + {ai_count} AI-generated images for {images.markers_covered} markers")
    else:
        print_success(f"Gathered {images.downloaded_count} images for {images.markers_covered} markers")

    if save_artifacts:
        images_metadata = config.paths.images_dir / f"images_{timestamp}.json"
        images_metadata.write_text(images.model_dump_json(indent=2))

    # Stage 5: Ken Burns motion
    print_info("\n[Stage 5/6] Generating motion parameters...")
    engine = KenBurnsEngine(intensity=ken_burns_intensity)
    render_spec = engine.create_render_spec(script, audio, images, str(output))
    render_spec = engine.add_variety(render_spec)

    print_success(f"Created render spec: {render_spec.segment_count} segments")

    if save_artifacts:
        spec_path = config.paths.artifacts_dir / f"render_spec_{timestamp}.json"
        spec_path.write_text(render_spec.model_dump_json(indent=2))

    # Stage 6: Render video
    print_info("\n[Stage 6/6] Rendering video...")
    renderer = VideoRenderer()
    success = renderer.render(render_spec)

    if not success:
        print_error("Failed to render video")
        raise typer.Exit(1)

    renderer.cleanup_temp_files(render_spec)

    print_success(f"\nVideo generated successfully!")
    console.print(f"\n[bold green]Output:[/bold green] {output}")
    console.print(f"Duration: {audio.total_duration:.1f}s")
    console.print(f"Resolution: {video_resolution[0]}x{video_resolution[1]} @ {fps}fps")

    # Stage 7: Publish to TikTok (optional)
    if publish:
        print_info("\n[Stage 7/7] Publishing to TikTok...")
        from ai_ken_burns.publish.tiktok import publish_to_tiktok, export_cookies_instructions

        result = publish_to_tiktok(
            video_path=output,
            title=script.title,
            thesis=research.thesis,
            headless=publish_headless,
        )

        if result.success:
            print_success("Video published to TikTok!")
        else:
            print_error(f"TikTok upload failed: {result.error}")
            if "cookies" in result.error.lower():
                console.print("\n[yellow]Cookie Setup Instructions:[/yellow]")
                console.print(export_cookies_instructions())

    log_timing_summary()
    raise typer.Exit(0)


@app.command("research-only")
def research_only(
    topic: Optional[str] = typer.Option(
        None,
        "--topic",
        "-t",
        help="Topic to filter news",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON file path",
    ),
    max_stories: int = typer.Option(
        5,
        "--max-stories",
        "-n",
        min=1,
        max=20,
        help="Maximum stories to analyze",
    ),
    min_relevance: float = typer.Option(
        0.1,
        "--min-relevance",
        min=0.0,
        max=1.0,
        help="Minimum relevance score (0-1)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Run research pipeline only (news to historical connection).

    Fetches news, scores for class consciousness relevance, and finds
    historical parallels using LLM analysis.

    Outputs a JSON file with news story and historical connection.

    Examples:

        ai-ken-burns research-only

        ai-ken-burns research-only --topic "workers" --output research.json

        ai-ken-burns research-only --max-stories 10 --min-relevance 0.2
    """
    print_banner()

    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    try:
        validate_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    config = get_config()

    # Set default output path
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = config.paths.research_dir / f"research_{timestamp}.json"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    print_info(f"Research output: {output}")
    if topic:
        print_info(f"Topic filter: {topic}")

    # Import research pipeline
    from ai_ken_burns.research.news_fetcher import NewsFetcher
    from ai_ken_burns.research.historical_connector import HistoricalConnector

    # Step 1: Fetch and score news
    print_info("Fetching news stories...")
    fetcher = NewsFetcher()
    stories = fetcher.get_top_stories(
        topic=topic,
        min_relevance=min_relevance,
        max_stories=max_stories,
    )

    if not stories:
        print_error("No relevant news stories found")
        raise typer.Exit(1)

    print_success(f"Found {len(stories)} relevant stories")

    # Display top stories
    console.print("\n[bold]Top Stories:[/bold]")
    for i, story in enumerate(stories[:5], 1):
        console.print(f"  {i}. {story.title[:60]}...")
        console.print(f"     Relevance: {story.relevance_score:.2f} | Themes: {', '.join(story.themes)}")

    # Step 2: Find historical connection
    print_info("\nFinding historical connection...")
    connector = HistoricalConnector()
    research_output = connector.find_best_connection(stories, topic=topic)

    if not research_output:
        print_error("Failed to find historical connection")
        raise typer.Exit(1)

    print_success(
        f"Found connection: {research_output.historical_event.name} "
        f"(confidence: {research_output.confidence_score:.2f})"
    )

    # Display result
    console.print("\n[bold]Research Result:[/bold]")
    console.print(f"  News: {research_output.news_story.title}")
    console.print(f"  Historical Event: {research_output.historical_event.name}")
    if research_output.historical_event.year:
        console.print(f"  Year: {research_output.historical_event.year}")
    console.print(f"  Location: {research_output.historical_event.location}")
    console.print(f"\n  Thesis: {research_output.thesis}")

    # Save output
    try:
        output_data = research_output.model_dump_json(indent=2)
        output.write_text(output_data)
        print_success(f"Research saved to {output}")
    except Exception as e:
        print_error(f"Failed to save research: {e}")
        raise typer.Exit(1)

    log_timing_summary()
    raise typer.Exit(0)


@app.command("script-only")
def script_only(
    research_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Research JSON file from research-only command",
    ),
    style: str = typer.Option(
        "documentary style, thoughtful and engaging",
        "--style",
        "-s",
        help="Style prompt for the narrative",
    ),
    target_duration: int = typer.Option(
        90,
        "--duration",
        "-d",
        min=30,
        max=300,
        help="Target duration in seconds",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output script file path",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Generate script from existing research.

    Takes a research JSON file and generates an annotated script
    with visual markers for Ken Burns video generation.

    Examples:

        ai-ken-burns script-only research.json

        ai-ken-burns script-only research.json --style "urgent, passionate"

        ai-ken-burns script-only research.json --duration 120
    """
    print_banner()

    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    try:
        validate_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    config = get_config()

    # Load research file
    try:
        from ai_ken_burns.research.models import ResearchOutput
        with open(research_file) as f:
            research_data = json.load(f)
        research = ResearchOutput.model_validate(research_data)
        print_success(f"Loaded research from {research_file}")
    except Exception as e:
        print_error(f"Failed to load research file: {e}")
        raise typer.Exit(1)

    # Set default output path
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = config.paths.scripts_dir / f"script_{timestamp}.json"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    print_info(f"Script output: {output}")
    print_info(f"Style: {style}")
    print_info(f"Target duration: {target_duration}s")

    # Generate script
    from ai_ken_burns.script.generator import ScriptGenerator

    print_info("Generating script...")
    generator = ScriptGenerator()
    script = generator.generate(
        research=research,
        style=style,
        target_duration=target_duration,
    )

    if not script:
        print_error("Failed to generate script")
        raise typer.Exit(1)

    print_success(f"Generated script: {script.title}")

    # Display result
    console.print("\n[bold]Script Summary:[/bold]")
    console.print(f"  Title: {script.title}")
    console.print(f"  Segments: {script.segment_count}")
    console.print(f"  Visual Markers: {script.marker_count}")
    console.print(f"  Estimated Duration: {script.estimate_duration():.0f}s")
    console.print(f"  Tone: {script.tone}")

    console.print("\n[bold]Visual Markers:[/bold]")
    for marker in script.all_markers[:5]:
        console.print(f"  [{marker.id}] {marker.description[:50]}...")
        console.print(f"       Type: {marker.visual_type.value} | Motion: {marker.motion.value}")

    if script.marker_count > 5:
        console.print(f"  ... and {script.marker_count - 5} more markers")

    # Save output
    try:
        output_data = script.model_dump_json(indent=2)
        output.write_text(output_data)
        print_success(f"Script saved to {output}")
    except Exception as e:
        print_error(f"Failed to save script: {e}")
        raise typer.Exit(1)

    log_timing_summary()
    raise typer.Exit(0)


@app.command("audio-only")
def audio_only(
    script_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Script JSON file from script-only command",
    ),
    voice: str = typer.Option(
        "onyx",
        "--voice",
        help="TTS voice (alloy, echo, fable, onyx, nova, shimmer)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for audio files",
    ),
    segmented: bool = typer.Option(
        True,
        "--segmented/--full",
        help="Generate per-segment audio for precise timing",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Generate audio from a script using OpenAI TTS.

    Takes a script JSON file and generates narration audio
    with timing information for visual marker synchronization.

    Examples:

        ai-ken-burns audio-only script.json

        ai-ken-burns audio-only script.json --voice nova

        ai-ken-burns audio-only script.json --output-dir ./audio
    """
    print_banner()

    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    try:
        validate_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    config = get_config()

    # Load script file
    try:
        from ai_ken_burns.script.models import AnnotatedScript
        with open(script_file) as f:
            script_data = json.load(f)
        script = AnnotatedScript.model_validate(script_data)
        print_success(f"Loaded script from {script_file}")
    except Exception as e:
        print_error(f"Failed to load script file: {e}")
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = config.paths.audio_dir / f"audio_{timestamp}"
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print_info(f"Audio output directory: {output_dir}")
    print_info(f"Voice: {voice}")
    print_info(f"Mode: {'segmented' if segmented else 'full'}")

    # Generate audio
    from ai_ken_burns.audio.tts_generator import TTSGenerator

    print_info("Generating audio...")
    generator = TTSGenerator(voice=voice)
    audio_output = generator.generate(
        script=script,
        output_dir=output_dir,
        generate_segments=segmented,
    )

    if not audio_output:
        print_error("Failed to generate audio")
        raise typer.Exit(1)

    print_success(f"Audio generated: {audio_output.total_duration:.1f}s")

    # Display result
    console.print("\n[bold]Audio Summary:[/bold]")
    console.print(f"  Main File: {audio_output.audio_file}")
    console.print(f"  Duration: {audio_output.total_duration:.1f}s")
    console.print(f"  Segments: {audio_output.segment_count}")
    console.print(f"  Markers: {len(audio_output.marker_times)}")
    if audio_output.average_wpm:
        console.print(f"  Speaking Rate: {audio_output.average_wpm:.0f} WPM")

    console.print("\n[bold]Marker Timing:[/bold]")
    for marker_id, (start, end) in list(audio_output.marker_times.items())[:5]:
        console.print(f"  [{marker_id}] {start:.1f}s - {end:.1f}s ({end - start:.1f}s)")

    if len(audio_output.marker_times) > 5:
        console.print(f"  ... and {len(audio_output.marker_times) - 5} more markers")

    # Save audio metadata
    metadata_path = output_dir / "audio_metadata.json"
    try:
        metadata = audio_output.model_dump_json(indent=2)
        metadata_path.write_text(metadata)
        print_success(f"Metadata saved to {metadata_path}")
    except Exception as e:
        print_error(f"Failed to save metadata: {e}")

    log_timing_summary()
    raise typer.Exit(0)


@app.command("images-only")
def images_only(
    script_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Script JSON file from script-only command",
    ),
    images_dir: Optional[Path] = typer.Option(
        None,
        "--local-images",
        "-l",
        exists=True,
        file_okay=False,
        help="Use local images from this directory instead of searching",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for downloaded images",
    ),
    images_per_marker: int = typer.Option(
        3,
        "--per-marker",
        "-n",
        min=1,
        max=10,
        help="Number of images to find per marker",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Gather images for a script's visual markers.

    Searches for images online or uses local images from a directory.

    Examples:

        ai-ken-burns images-only script.json

        ai-ken-burns images-only script.json --local-images ./my_photos

        ai-ken-burns images-only script.json --per-marker 5
    """
    print_banner()

    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    config = get_config()

    # Load script file
    try:
        from ai_ken_burns.script.models import AnnotatedScript
        with open(script_file) as f:
            script_data = json.load(f)
        script = AnnotatedScript.model_validate(script_data)
        print_success(f"Loaded script from {script_file}")
    except Exception as e:
        print_error(f"Failed to load script file: {e}")
        raise typer.Exit(1)

    print_info(f"Script has {script.marker_count} visual markers")

    # Set default output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = config.paths.images_dir / f"images_{timestamp}"
    output_dir = output_dir.resolve()

    # Gather images
    from ai_ken_burns.images.manager import ImageManager

    manager = ImageManager(images_dir=output_dir)

    if images_dir:
        print_info(f"Using local images from: {images_dir}")
        collection = manager.use_local_images(script, images_dir)
    else:
        print_info("Searching for images online...")
        collection = manager.gather_images(script, images_per_marker=images_per_marker)

    manager.close()

    print_success(f"Image collection complete!")

    # Display result
    console.print("\n[bold]Image Collection:[/bold]")
    console.print(f"  Total Images: {collection.image_count}")
    console.print(f"  Downloaded: {collection.downloaded_count}")
    console.print(f"  Markers Covered: {collection.markers_covered}/{script.marker_count}")
    console.print(f"  Images Dir: {collection.images_dir}")

    console.print("\n[bold]Selected Images:[/bold]")
    for marker_id, image_id in list(collection.marker_images.items())[:5]:
        img = collection.get_image_for_marker(marker_id)
        if img:
            console.print(f"  [{marker_id}] {img.title[:40]}...")
            console.print(f"       Source: {img.source_name} | Size: {img.width}x{img.height}")

    if len(collection.marker_images) > 5:
        console.print(f"  ... and {len(collection.marker_images) - 5} more")

    # Save collection metadata
    metadata_path = output_dir / "collection.json"
    try:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(collection.model_dump_json(indent=2))
        print_success(f"Collection saved to {metadata_path}")
    except Exception as e:
        print_error(f"Failed to save collection: {e}")

    log_timing_summary()
    raise typer.Exit(0)


@app.command("render-only")
def render_only(
    script_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Script JSON file",
    ),
    audio_metadata: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Audio metadata JSON file",
    ),
    images_collection: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Images collection JSON file",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output video file path",
    ),
    ken_burns_intensity: float = typer.Option(
        0.5,
        "--intensity",
        "-k",
        min=0.0,
        max=1.0,
        help="Ken Burns effect intensity",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Render video from existing script, audio, and images.

    Takes pre-generated artifacts and produces the final video.

    Examples:

        ai-ken-burns render-only script.json audio_metadata.json collection.json

        ai-ken-burns render-only script.json audio.json images.json -o output.mp4
    """
    print_banner()

    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    config = get_config()

    # Load script
    try:
        from ai_ken_burns.script.models import AnnotatedScript
        with open(script_file) as f:
            script = AnnotatedScript.model_validate(json.load(f))
        print_success(f"Loaded script: {script.title}")
    except Exception as e:
        print_error(f"Failed to load script: {e}")
        raise typer.Exit(1)

    # Load audio metadata
    try:
        from ai_ken_burns.audio.models import AudioOutput
        with open(audio_metadata) as f:
            audio = AudioOutput.model_validate(json.load(f))
        print_success(f"Loaded audio: {audio.total_duration:.1f}s")
    except Exception as e:
        print_error(f"Failed to load audio metadata: {e}")
        raise typer.Exit(1)

    # Load images collection
    try:
        from ai_ken_burns.images.models import ImageCollection
        with open(images_collection) as f:
            images = ImageCollection.model_validate(json.load(f))
        print_success(f"Loaded images: {images.image_count} images")
    except Exception as e:
        print_error(f"Failed to load images collection: {e}")
        raise typer.Exit(1)

    # Set output path
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = config.paths.output_dir / f"video_{timestamp}.mp4"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    print_info(f"Output: {output}")
    print_info(f"Ken Burns intensity: {ken_burns_intensity}")

    # Generate render spec
    from ai_ken_burns.video.ken_burns import KenBurnsEngine
    from ai_ken_burns.video.renderer import VideoRenderer

    print_info("Generating motion parameters...")
    engine = KenBurnsEngine(intensity=ken_burns_intensity)
    render_spec = engine.create_render_spec(script, audio, images, str(output))
    render_spec = engine.add_variety(render_spec)

    print_success(f"Render spec: {render_spec.segment_count} segments")

    # Render video
    print_info("Rendering video...")
    renderer = VideoRenderer()
    success = renderer.render(render_spec)

    if not success:
        print_error("Failed to render video")
        raise typer.Exit(1)

    renderer.cleanup_temp_files(render_spec)

    print_success(f"\nVideo rendered successfully!")
    console.print(f"\n[bold green]Output:[/bold green] {output}")
    console.print(f"Duration: {audio.total_duration:.1f}s")

    log_timing_summary()
    raise typer.Exit(0)


@app.command()
def info() -> None:
    """Show configuration and system status."""
    print_banner()

    try:
        config = get_config()
        errors = config.validate()
    except Exception as e:
        print_error(f"Configuration error: {e}")
        config = None
        errors = [str(e)]

    # Status table
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # OpenAI API
    if config and config.llm.api_key:
        api_key_preview = config.llm.api_key[:8] + "..." + config.llm.api_key[-4:]
        table.add_row("OpenAI API", "[green]OK[/green]", api_key_preview)
    else:
        table.add_row("OpenAI API", "[red]MISSING[/red]", "Set OPENAI_API_KEY")

    # FFmpeg
    try:
        from ai_ken_burns.utils.ffmpeg_utils import check_ffmpeg
        ffmpeg_ok, ffmpeg_version = check_ffmpeg()
        if ffmpeg_ok:
            table.add_row("FFmpeg", "[green]OK[/green]", ffmpeg_version)
        else:
            table.add_row("FFmpeg", "[red]MISSING[/red]", "Install FFmpeg")
    except ImportError:
        table.add_row("FFmpeg", "[yellow]?[/yellow]", "ffmpeg_utils not loaded")

    # Directories
    if config:
        table.add_row("Artifacts Dir", "[green]OK[/green]", str(config.paths.artifacts_dir))
        table.add_row("Output Dir", "[green]OK[/green]", str(config.paths.output_dir))

    console.print(table)

    # Configuration details
    if config:
        console.print("\n")
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value")

        config_table.add_row("Research Model", config.llm.research_model)
        config_table.add_row("Generation Model", config.llm.generation_model)
        config_table.add_row("TTS Model", config.tts.model)
        config_table.add_row("TTS Voice", config.tts.voice)
        config_table.add_row("Video Resolution", f"{config.video.width}x{config.video.height}")
        config_table.add_row("Video FPS", str(config.video.fps))
        config_table.add_row("Ken Burns Intensity", str(config.ken_burns.intensity))

        console.print(config_table)

    # Errors
    if errors:
        console.print("\n[bold red]Configuration Errors:[/bold red]")
        for error in errors:
            print_error(error)


@app.command()
def validate() -> None:
    """Validate configuration and dependencies."""
    print_banner()
    print_info("Validating configuration...")

    errors = []

    # Check config
    try:
        config = get_config()
        errors.extend(config.validate())
    except Exception as e:
        errors.append(f"Configuration load error: {e}")

    # Check FFmpeg
    try:
        from ai_ken_burns.utils.ffmpeg_utils import check_ffmpeg
        ffmpeg_ok, _ = check_ffmpeg()
        if not ffmpeg_ok:
            errors.append("FFmpeg not found in PATH")
    except ImportError:
        errors.append("ffmpeg_utils module not available")

    # Report results
    if errors:
        print_error("Validation failed:")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)
    else:
        print_success("All validations passed!")
        raise typer.Exit(0)


@app.command("publish")
def publish_video(
    video_file: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Video file to publish",
    ),
    description: str = typer.Option(
        ...,
        "--description",
        "-d",
        help="Video description/caption",
    ),
    hashtags: Optional[str] = typer.Option(
        None,
        "--hashtags",
        help="Comma-separated hashtags (without #)",
    ),
    cookies: Optional[Path] = typer.Option(
        None,
        "--cookies",
        "-c",
        exists=True,
        help="Path to TikTok cookies file",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--visible",
        help="Run browser in headless mode",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Publish a video to TikTok.

    Requires TikTok cookies exported from your browser.

    Examples:

        ai-ken-burns publish video.mp4 -d "My documentary"

        ai-ken-burns publish video.mp4 -d "History lesson" --hashtags "history,labor"

        ai-ken-burns publish video.mp4 -d "Test" --visible  # Show browser
    """
    print_banner()

    if verbose:
        set_log_level("DEBUG")
    else:
        set_log_level("INFO")

    from ai_ken_burns.publish.tiktok import TikTokPublisher, export_cookies_instructions

    # Parse hashtags
    hashtag_list = None
    if hashtags:
        hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()]

    print_info(f"Publishing: {video_file.name}")
    print_info(f"Description: {description[:50]}...")
    if hashtag_list:
        print_info(f"Hashtags: {', '.join(hashtag_list)}")

    publisher = TikTokPublisher(cookies_path=cookies, headless=headless)

    # Validate cookies first
    if not publisher.validate_cookies():
        print_error("Invalid or missing TikTok cookies file")
        console.print("\n[yellow]Setup Instructions:[/yellow]")
        console.print(export_cookies_instructions())
        raise typer.Exit(1)

    result = publisher.publish(
        video_path=video_file,
        description=description,
        hashtags=hashtag_list,
    )

    if result.success:
        print_success("Video published to TikTok successfully!")
        raise typer.Exit(0)
    else:
        print_error(f"Upload failed: {result.error}")
        raise typer.Exit(1)


@app.command("tiktok-setup")
def tiktok_setup() -> None:
    """Show instructions for setting up TikTok publishing."""
    print_banner()

    from ai_ken_burns.publish.tiktok import export_cookies_instructions, TikTokPublisher

    console.print("[bold]TikTok Publishing Setup[/bold]\n")

    # Check current status
    publisher = TikTokPublisher()
    if publisher.validate_cookies():
        print_success(f"TikTok cookies found: {publisher.cookies_path}")
        console.print("You're ready to publish videos!")
    else:
        print_warning("TikTok cookies not configured")
        console.print(export_cookies_instructions())


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

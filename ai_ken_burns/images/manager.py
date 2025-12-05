"""
Image manager for AI Ken Burns.

Handles downloading, caching, and managing images for video generation.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image

from ai_ken_burns.config import get_config
from ai_ken_burns.script.models import AnnotatedScript, VisualMarker
from ai_ken_burns.images.models import ImageResult, ImageCollection
from ai_ken_burns.images.searcher import ImageSearcher
from ai_ken_burns.utils.logging_utils import get_logger, log_timing

logger = get_logger("ai_ken_burns.images")


class ImageManager:
    """
    Manages images for video generation.

    Handles:
    - Searching for images based on visual markers
    - Downloading and caching images
    - Validating image dimensions
    - Creating image collections for video rendering
    """

    def __init__(
        self,
        images_dir: Optional[Path] = None,
        min_width: int = 1280,
        min_height: int = 720,
    ) -> None:
        """
        Initialize the image manager.

        Args:
            images_dir: Directory for storing images
            min_width: Minimum acceptable image width
            min_height: Minimum acceptable image height
        """
        self.config = get_config()
        self.images_dir = images_dir or Path(self.config.paths.images_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.min_width = min_width
        self.min_height = min_height

        self.searcher = ImageSearcher()
        self.http_client = httpx.Client(timeout=60)

    def gather_images(
        self,
        script: AnnotatedScript,
        images_per_marker: int = 3,
    ) -> ImageCollection:
        """
        Gather images for all visual markers in a script.

        Args:
            script: AnnotatedScript with visual markers
            images_per_marker: Number of images to find per marker

        Returns:
            ImageCollection with all images
        """
        logger.info(f"Gathering images for script: {script.title}")

        # Create project directory
        project_id = hashlib.md5(script.title.encode()).hexdigest()[:8]
        project_dir = self.images_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        collection = ImageCollection(
            project_id=project_id,
            script_title=script.title,
            images_dir=str(project_dir),
        )

        # Get all markers
        markers = script.all_markers

        logger.info(f"Searching images for {len(markers)} markers...")

        for marker in markers:
            with log_timing(f"search_images_{marker.id}", logger):
                results = self.searcher.search_for_marker(
                    marker,
                    max_results=images_per_marker,
                )

            if not results:
                logger.warning(f"No images found for marker [{marker.id}]")
                continue

            # Download best result
            best_result = results[0]
            downloaded = self._download_image(best_result, project_dir)

            if downloaded:
                collection.add_image(downloaded, select_for_marker=True)

                # Add remaining results without downloading yet
                for result in results[1:]:
                    collection.images.append(result)

        logger.info(
            f"Image collection complete: {collection.downloaded_count}/{collection.image_count} downloaded, "
            f"{collection.markers_covered} markers covered"
        )

        return collection

    def _download_image(
        self,
        result: ImageResult,
        output_dir: Path,
    ) -> Optional[ImageResult]:
        """
        Download an image and update the result.

        Args:
            result: ImageResult with source URL
            output_dir: Directory to save image

        Returns:
            Updated ImageResult with local path, or None if failed
        """
        try:
            logger.debug(f"Downloading: {result.source_url[:60]}...")

            response = self.http_client.get(result.source_url, follow_redirects=True)
            response.raise_for_status()

            # Determine file extension
            content_type = response.headers.get("content-type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                ext = ".jpg"
            elif "png" in content_type:
                ext = ".png"
            elif "gif" in content_type:
                ext = ".gif"
            elif "webp" in content_type:
                ext = ".webp"
            else:
                ext = ".jpg"  # Default

            # Save to file
            filename = f"{result.marker_id}_{result.id}{ext}"
            filepath = output_dir / filename

            with open(filepath, "wb") as f:
                f.write(response.content)

            # Validate and get dimensions
            try:
                with Image.open(filepath) as img:
                    width, height = img.size

                    # Check minimum dimensions
                    if width < self.min_width or height < self.min_height:
                        logger.debug(
                            f"Image too small: {width}x{height} "
                            f"(min: {self.min_width}x{self.min_height})"
                        )
                        # Keep it anyway for now, can upscale later

                    result.width = width
                    result.height = height

            except Exception as e:
                logger.warning(f"Could not read image dimensions: {e}")

            result.local_path = str(filepath)
            result.is_downloaded = True

            logger.debug(f"Downloaded: {filepath.name} ({result.width}x{result.height})")
            return result

        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None

    def download_all(
        self,
        collection: ImageCollection,
    ) -> ImageCollection:
        """
        Download all images in a collection.

        Args:
            collection: ImageCollection with images to download

        Returns:
            Updated ImageCollection
        """
        output_dir = Path(collection.images_dir) if collection.images_dir else self.images_dir

        for image in collection.images:
            if image.is_downloaded:
                continue

            downloaded = self._download_image(image, output_dir)
            if downloaded:
                # Update in place
                image.local_path = downloaded.local_path
                image.is_downloaded = True
                image.width = downloaded.width
                image.height = downloaded.height

        return collection

    def use_local_images(
        self,
        script: AnnotatedScript,
        images_dir: Path,
    ) -> ImageCollection:
        """
        Use local images from a directory instead of searching.

        Matches images to markers based on filename patterns or order.

        Args:
            script: AnnotatedScript with visual markers
            images_dir: Directory containing images

        Returns:
            ImageCollection with local images
        """
        logger.info(f"Using local images from: {images_dir}")

        project_id = hashlib.md5(script.title.encode()).hexdigest()[:8]

        collection = ImageCollection(
            project_id=project_id,
            script_title=script.title,
            images_dir=str(images_dir),
        )

        # Get all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        image_files = sorted([
            f for f in images_dir.iterdir()
            if f.suffix.lower() in image_extensions
        ])

        markers = script.all_markers

        # Try to match by filename pattern first
        unmatched_markers = []
        for marker in markers:
            matched = False
            for img_file in image_files:
                if marker.id in img_file.stem.lower():
                    result = self._create_local_result(marker, img_file)
                    if result:
                        collection.add_image(result, select_for_marker=True)
                        matched = True
                        break

            if not matched:
                unmatched_markers.append(marker)

        # Assign remaining images to unmatched markers in order
        available_files = [
            f for f in image_files
            if not any(f.stem.lower() in (img.local_path or "") for img in collection.images)
        ]

        for marker, img_file in zip(unmatched_markers, available_files):
            result = self._create_local_result(marker, img_file)
            if result:
                collection.add_image(result, select_for_marker=True)

        logger.info(
            f"Local collection: {collection.image_count} images, "
            f"{collection.markers_covered}/{len(markers)} markers covered"
        )

        return collection

    def _create_local_result(
        self,
        marker: VisualMarker,
        image_path: Path,
    ) -> Optional[ImageResult]:
        """Create ImageResult from a local file."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size

            return ImageResult(
                id=hashlib.md5(str(image_path).encode()).hexdigest()[:12],
                marker_id=marker.id,
                source_url=f"file://{image_path}",
                source_name="Local",
                title=image_path.stem,
                local_path=str(image_path),
                is_downloaded=True,
                width=width,
                height=height,
                description=marker.description,
                relevance_score=1.0,
            )

        except Exception as e:
            logger.error(f"Failed to read local image {image_path}: {e}")
            return None

    def close(self) -> None:
        """Clean up resources."""
        self.searcher.close()
        self.http_client.close()

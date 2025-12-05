"""
Data models for image pipeline.

Defines structures for image search results and collections.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ImageResult(BaseModel):
    """
    A single image search result.

    Contains metadata about the image and its local path after download.
    """

    # Identification
    id: str = Field(description="Unique image ID")
    marker_id: str = Field(description="Associated visual marker ID")

    # Source info
    source_url: str = Field(description="Original image URL")
    source_name: str = Field(default="", description="Source website/archive name")
    title: str = Field(default="", description="Image title or caption")

    # Local file
    local_path: Optional[str] = Field(
        default=None,
        description="Local file path after download"
    )
    is_downloaded: bool = Field(default=False, description="Whether image is downloaded")

    # Dimensions
    width: Optional[int] = Field(default=None, description="Image width in pixels")
    height: Optional[int] = Field(default=None, description="Image height in pixels")

    # Metadata
    description: str = Field(default="", description="Image description")
    era: Optional[str] = Field(default=None, description="Historical era")
    date: Optional[str] = Field(default=None, description="Date of the image/event")

    # Quality metrics
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to the visual marker"
    )

    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate aspect ratio."""
        if self.width and self.height:
            return self.width / self.height
        return None

    @property
    def is_landscape(self) -> bool:
        """Check if image is landscape orientation."""
        ratio = self.aspect_ratio
        return ratio is not None and ratio > 1.0

    @property
    def is_usable(self) -> bool:
        """Check if image is ready to use."""
        return self.is_downloaded and self.local_path is not None


class ImageCollection(BaseModel):
    """
    Collection of images for a video project.

    Maps visual markers to their selected images.
    """

    # Project info
    project_id: str = Field(description="Project identifier")
    script_title: str = Field(default="", description="Associated script title")

    # Images
    images: list[ImageResult] = Field(
        default_factory=list,
        description="All images in the collection"
    )

    # Marker mapping
    marker_images: dict[str, str] = Field(
        default_factory=dict,
        description="Map of marker_id to selected image_id"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When collection was created"
    )
    images_dir: Optional[str] = Field(
        default=None,
        description="Directory containing downloaded images"
    )

    @property
    def image_count(self) -> int:
        """Total number of images."""
        return len(self.images)

    @property
    def downloaded_count(self) -> int:
        """Number of downloaded images."""
        return sum(1 for img in self.images if img.is_downloaded)

    @property
    def markers_covered(self) -> int:
        """Number of markers with assigned images."""
        return len(self.marker_images)

    def get_image_for_marker(self, marker_id: str) -> Optional[ImageResult]:
        """Get the selected image for a marker."""
        image_id = self.marker_images.get(marker_id)
        if not image_id:
            return None

        for img in self.images:
            if img.id == image_id:
                return img
        return None

    def add_image(self, image: ImageResult, select_for_marker: bool = True) -> None:
        """Add an image to the collection."""
        self.images.append(image)
        if select_for_marker and image.marker_id:
            self.marker_images[image.marker_id] = image.id

    def get_ordered_images(self, marker_ids: list[str]) -> list[ImageResult]:
        """Get images in order of marker IDs."""
        ordered = []
        for marker_id in marker_ids:
            img = self.get_image_for_marker(marker_id)
            if img:
                ordered.append(img)
        return ordered

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

"""
TikTok publisher for AI Ken Burns.

Uses tiktok-uploader library to automatically post videos to TikTok.
Requires browser cookies for authentication.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from ai_ken_burns.config import get_config
from ai_ken_burns.utils.logging_utils import get_logger

logger = get_logger("ai_ken_burns.publish.tiktok")


@dataclass
class TikTokUploadResult:
    """Result of a TikTok upload attempt."""

    success: bool
    video_path: str
    error: Optional[str] = None
    video_url: Optional[str] = None


class TikTokPublisher:
    """
    Publishes videos to TikTok using browser automation.

    Requires TikTok cookies file for authentication. The cookies can be
    exported from your browser after logging into TikTok.

    Cookie file format (cookies.txt or cookies.json):
    - JSON format: [{"name": "sessionid", "value": "...", ...}, ...]
    - Netscape format: Standard cookies.txt format
    """

    def __init__(
        self,
        cookies_path: Optional[Path] = None,
        headless: bool = True,
    ) -> None:
        """
        Initialize the TikTok publisher.

        Args:
            cookies_path: Path to cookies file. If None, looks for:
                         1. TIKTOK_COOKIES_PATH environment variable
                         2. ~/.tiktok_cookies.json
                         3. ./tiktok_cookies.json
            headless: Run browser in headless mode (no visible window)
        """
        self.config = get_config()
        self.headless = headless
        self.cookies_path = self._find_cookies(cookies_path)

        if self.cookies_path:
            logger.info(f"Using TikTok cookies from: {self.cookies_path}")
        else:
            logger.warning("No TikTok cookies file found. Upload will fail.")

    def _find_cookies(self, provided_path: Optional[Path]) -> Optional[Path]:
        """Find the cookies file from various locations."""
        # Check provided path
        if provided_path and provided_path.exists():
            return provided_path

        # Check environment variable
        env_path = os.getenv("TIKTOK_COOKIES_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path

        # Check common locations
        search_paths = [
            Path.home() / ".tiktok_cookies.json",
            Path.home() / "tiktok_cookies.json",
            Path.cwd() / "tiktok_cookies.json",
            Path.cwd() / "cookies.json",
            self.config.paths.base_dir / "tiktok_cookies.json",
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def publish(
        self,
        video_path: Path,
        description: str,
        hashtags: Optional[list[str]] = None,
        schedule_time: Optional[int] = None,
    ) -> TikTokUploadResult:
        """
        Publish a video to TikTok.

        Args:
            video_path: Path to the video file
            description: Video description/caption
            hashtags: List of hashtags (without #)
            schedule_time: Unix timestamp to schedule the post (optional)

        Returns:
            TikTokUploadResult with success status
        """
        video_path = Path(video_path)

        if not video_path.exists():
            return TikTokUploadResult(
                success=False,
                video_path=str(video_path),
                error=f"Video file not found: {video_path}",
            )

        if not self.cookies_path:
            return TikTokUploadResult(
                success=False,
                video_path=str(video_path),
                error="No TikTok cookies file found. Please export your browser cookies.",
            )

        # Build full description with hashtags
        full_description = description
        if hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
            full_description = f"{description}\n\n{hashtag_str}"

        logger.info(f"Uploading to TikTok: {video_path.name}")
        logger.info(f"Description: {description[:50]}...")

        try:
            from tiktok_uploader.upload import upload_video
            from tiktok_uploader.auth import AuthBackend

            # Upload the video
            upload_video(
                filename=str(video_path),
                description=full_description,
                cookies=str(self.cookies_path),
                headless=self.headless,
                schedule_time=schedule_time,
            )

            logger.info("TikTok upload successful!")

            return TikTokUploadResult(
                success=True,
                video_path=str(video_path),
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"TikTok upload failed: {error_msg}")

            return TikTokUploadResult(
                success=False,
                video_path=str(video_path),
                error=error_msg,
            )

    def validate_cookies(self) -> bool:
        """Check if cookies file exists and is valid."""
        if not self.cookies_path:
            return False

        try:
            with open(self.cookies_path) as f:
                data = json.load(f)

            # Check for required cookie (sessionid)
            if isinstance(data, list):
                cookie_names = [c.get("name") for c in data]
                return "sessionid" in cookie_names

            return False

        except Exception as e:
            logger.error(f"Invalid cookies file: {e}")
            return False


def publish_to_tiktok(
    video_path: Path,
    title: str,
    thesis: Optional[str] = None,
    hashtags: Optional[list[str]] = None,
    cookies_path: Optional[Path] = None,
    headless: bool = True,
) -> TikTokUploadResult:
    """
    Convenience function to publish a video to TikTok.

    Args:
        video_path: Path to the video file
        title: Video title (used in description)
        thesis: Optional thesis statement to include
        hashtags: List of hashtags (default: class consciousness related)
        cookies_path: Optional path to cookies file
        headless: Run browser in headless mode

    Returns:
        TikTokUploadResult with success status
    """
    # Default hashtags for class consciousness content
    if hashtags is None:
        hashtags = [
            "history",
            "classconsciousness",
            "laborhistory",
            "workers",
            "documentary",
            "learnontiktok",
            "historytiktok",
        ]

    # Build description
    description = title
    if thesis:
        description = f"{title}\n\n{thesis}"

    publisher = TikTokPublisher(cookies_path=cookies_path, headless=headless)
    return publisher.publish(
        video_path=video_path,
        description=description,
        hashtags=hashtags,
    )


def export_cookies_instructions() -> str:
    """Return instructions for exporting TikTok cookies."""
    return """
To publish videos to TikTok, you need to export your browser cookies:

1. Install a browser extension to export cookies:
   - Chrome: "Get cookies.txt LOCALLY" or "Cookie-Editor"
   - Firefox: "cookies.txt" or "Cookie-Editor"

2. Log into TikTok in your browser

3. Export cookies from tiktok.com:
   - If using Cookie-Editor: Export as JSON
   - If using cookies.txt: Export as Netscape format

4. Save the file as one of:
   - ~/.tiktok_cookies.json (recommended)
   - ./tiktok_cookies.json
   - Or set TIKTOK_COOKIES_PATH environment variable

5. The cookies file should contain at least the 'sessionid' cookie

Note: TikTok cookies expire after ~2 months. You'll need to re-export them
periodically.
"""

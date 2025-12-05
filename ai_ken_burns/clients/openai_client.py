"""
OpenAI API client wrapper with retry logic and error handling.

Provides a unified interface for GPT-4, TTS, and DALL-E API calls with:
- Exponential backoff retry logic
- Rate limit handling
- Structured error responses
- Request/response logging
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from openai import OpenAI, APIError, RateLimitError, APITimeoutError, APIConnectionError

from ai_ken_burns.config import get_config
from ai_ken_burns.utils.logging_utils import get_api_logger, log_timing

logger = get_api_logger()


@dataclass
class APIResponse:
    """Structured response from OpenAI API."""

    success: bool
    content: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None


class OpenAIClient:
    """
    Centralized OpenAI client with retry logic and error handling.

    Handles:
    - GPT-4 chat completions (for research and generation)
    - TTS API calls (for audio generation)
    - DALL-E image generation (for visual content)
    - Automatic retries with exponential backoff
    - Rate limit detection and handling
    """

    def __init__(self) -> None:
        self.config = get_config()
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not self.config.llm.api_key:
                raise ValueError("OpenAI API key not configured")
            self._client = OpenAI(api_key=self.config.llm.api_key)
        return self._client

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.config.llm.retry_delay_base * (2 ** attempt)
        return min(delay, self.config.llm.retry_delay_max)

    def _should_retry(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        return isinstance(error, (RateLimitError, APITimeoutError, APIConnectionError))

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_format: Optional[dict] = None,
        max_tokens: int = 4096,
    ) -> APIResponse:
        """
        Make a chat completion request with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to config research_model)
            temperature: Temperature for sampling
            response_format: Optional response format (e.g., {"type": "json_object"})
            max_tokens: Maximum tokens in response

        Returns:
            APIResponse with success status and content or error
        """
        model = model or self.config.llm.research_model
        temperature = temperature if temperature is not None else self.config.llm.temperature

        last_error: Optional[Exception] = None

        for attempt in range(self.config.llm.max_retries):
            try:
                start_time = time.perf_counter()

                logger.debug(
                    f"Chat completion request: model={model}, "
                    f"messages={len(messages)}, attempt={attempt + 1}"
                )

                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": self.config.llm.request_timeout,
                }

                if response_format:
                    kwargs["response_format"] = response_format

                response = self.client.chat.completions.create(**kwargs)

                latency_ms = (time.perf_counter() - start_time) * 1000

                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else None

                logger.debug(
                    f"Chat completion success: tokens={tokens_used}, "
                    f"latency={latency_ms:.0f}ms"
                )

                return APIResponse(
                    success=True,
                    content=content,
                    tokens_used=tokens_used,
                    model=model,
                    latency_ms=latency_ms,
                )

            except RateLimitError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"Rate limited. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except APITimeoutError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"Request timeout. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except APIConnectionError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"Connection error. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    error_type="api_error",
                    model=model,
                )

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    error_type="unexpected_error",
                    model=model,
                )

        # All retries exhausted
        error_msg = f"Max retries ({self.config.llm.max_retries}) exceeded"
        if last_error:
            error_msg += f": {last_error}"
        logger.error(error_msg)

        return APIResponse(
            success=False,
            error=error_msg,
            error_type="max_retries_exceeded",
            model=model,
        )

    def chat_completion_json(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> APIResponse:
        """
        Make a chat completion request expecting JSON response.

        Returns APIResponse with parsed JSON in 'data' field.
        """
        response = self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        if response.success and response.content:
            try:
                response.data = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                response.success = False
                response.error = f"JSON parse error: {e}"
                response.error_type = "json_parse_error"

        return response

    def text_to_speech(
        self,
        text: str,
        output_path: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> APIResponse:
        """
        Generate speech from text using OpenAI TTS API.

        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            model: TTS model (defaults to config)
            voice: Voice to use (defaults to config)
            speed: Speech speed (defaults to config)

        Returns:
            APIResponse with success status
        """
        model = model or self.config.tts.model
        voice = voice or self.config.tts.voice
        speed = speed if speed is not None else self.config.tts.speed

        last_error: Optional[Exception] = None

        for attempt in range(self.config.llm.max_retries):
            try:
                start_time = time.perf_counter()

                logger.debug(
                    f"TTS request: model={model}, voice={voice}, "
                    f"text_length={len(text)}, attempt={attempt + 1}"
                )

                response = self.client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=text,
                    speed=speed,
                    response_format=self.config.tts.response_format,
                )

                # Stream response to file
                response.stream_to_file(output_path)

                latency_ms = (time.perf_counter() - start_time) * 1000

                logger.debug(f"TTS success: output={output_path}, latency={latency_ms:.0f}ms")

                return APIResponse(
                    success=True,
                    content=output_path,
                    model=model,
                    latency_ms=latency_ms,
                )

            except RateLimitError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"TTS rate limited. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except (APITimeoutError, APIConnectionError) as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"TTS connection issue. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except APIError as e:
                logger.error(f"TTS API error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    error_type="api_error",
                    model=model,
                )

            except Exception as e:
                logger.error(f"TTS unexpected error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    error_type="unexpected_error",
                    model=model,
                )

        # All retries exhausted
        error_msg = f"TTS max retries ({self.config.llm.max_retries}) exceeded"
        if last_error:
            error_msg += f": {last_error}"
        logger.error(error_msg)

        return APIResponse(
            success=False,
            error=error_msg,
            error_type="max_retries_exceeded",
            model=model,
        )

    def generate_image(
        self,
        prompt: str,
        output_path: str,
        model: str = "dall-e-3",
        size: str = "1792x1024",
        quality: str = "standard",
        style: str = "natural",
    ) -> APIResponse:
        """
        Generate an image using DALL-E API.

        Args:
            prompt: Text description of the image to generate
            output_path: Path to save the generated image
            model: DALL-E model (dall-e-2 or dall-e-3)
            size: Image size (1024x1024, 1792x1024, 1024x1792 for dall-e-3)
            quality: Image quality (standard or hd for dall-e-3)
            style: Image style (natural or vivid for dall-e-3)

        Returns:
            APIResponse with success status and image URL/path
        """
        import httpx
        from pathlib import Path

        last_error: Optional[Exception] = None

        for attempt in range(self.config.llm.max_retries):
            try:
                start_time = time.perf_counter()

                logger.debug(
                    f"DALL-E request: model={model}, size={size}, "
                    f"prompt_length={len(prompt)}, attempt={attempt + 1}"
                )

                # Generate image
                response = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    n=1,
                )

                image_url = response.data[0].url
                revised_prompt = getattr(response.data[0], 'revised_prompt', None)

                # Download the image
                with httpx.Client(timeout=60, follow_redirects=True) as client:
                    img_response = client.get(image_url)
                    img_response.raise_for_status()

                    # Save to file
                    output_file = Path(output_path)
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(img_response.content)

                latency_ms = (time.perf_counter() - start_time) * 1000

                logger.debug(
                    f"DALL-E success: output={output_path}, "
                    f"latency={latency_ms:.0f}ms"
                )

                return APIResponse(
                    success=True,
                    content=str(output_path),
                    data={
                        "url": image_url,
                        "revised_prompt": revised_prompt,
                        "local_path": str(output_path),
                    },
                    model=model,
                    latency_ms=latency_ms,
                )

            except RateLimitError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"DALL-E rate limited. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except (APITimeoutError, APIConnectionError) as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"DALL-E connection issue. Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            except APIError as e:
                logger.error(f"DALL-E API error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    error_type="api_error",
                    model=model,
                )

            except Exception as e:
                logger.error(f"DALL-E unexpected error: {e}")
                return APIResponse(
                    success=False,
                    error=str(e),
                    error_type="unexpected_error",
                    model=model,
                )

        # All retries exhausted
        error_msg = f"DALL-E max retries ({self.config.llm.max_retries}) exceeded"
        if last_error:
            error_msg += f": {last_error}"
        logger.error(error_msg)

        return APIResponse(
            success=False,
            error=error_msg,
            error_type="max_retries_exceeded",
            model=model,
        )

    def generate_image_prompt(
        self,
        visual_description: str,
        historical_context: str,
        style_hints: Optional[str] = None,
    ) -> APIResponse:
        """
        Generate an optimized DALL-E prompt for a visual marker.

        Uses GPT-4 to create a detailed, evocative prompt that will
        produce high-quality documentary-style imagery.

        Args:
            visual_description: Description of what the image should show
            historical_context: Historical context for the image
            style_hints: Optional style guidance (e.g., "sepia toned", "archival")

        Returns:
            APIResponse with the generated prompt in content field
        """
        system_prompt = """You are an expert at crafting DALL-E image generation prompts
for documentary-style historical imagery. Your prompts should:

1. Create evocative, historically accurate imagery
2. Use cinematic composition and lighting
3. Avoid text, logos, or modern elements unless specifically relevant
4. Specify artistic style (photograph, painting, illustration)
5. Include mood and atmosphere details
6. Be detailed but under 400 characters for best results

Output ONLY the prompt text, no explanations or quotes."""

        user_prompt = f"""Create a DALL-E prompt for this documentary visual:

Description: {visual_description}
Historical Context: {historical_context}
{f'Style hints: {style_hints}' if style_hints else ''}

Generate a single, detailed image prompt."""

        response = self.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        if response.success and response.content:
            # Clean up the prompt (remove quotes if present)
            prompt = response.content.strip().strip('"\'')
            response.content = prompt

        return response


# Global client instance
_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get or create the global OpenAI client."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client

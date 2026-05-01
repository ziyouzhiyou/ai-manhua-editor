"""
Xiaomi MiMo API Integration
Supports all MiMo V2.5 models: reasoning, multimodal, voice
"""
import os
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
import aiohttp

logger = logging.getLogger(__name__)


class MiMoAPI:
    """
    Xiaomi MiMo API client
    Compatible with OpenAI-compatible API format
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("MIMO_API_KEY", "")
        self.base_url = base_url or os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=300)
            )
        return self.session

    async def chat_completion(self, 
                               system_prompt: str = "",
                               user_prompt: str = "",
                               model: str = "mimo-v2.5",
                               temperature: float = 0.7,
                               max_tokens: int = 2000,
                               stream: bool = False) -> str:
        """
        Send chat completion request to MiMo API

        Args:
            system_prompt: System instruction
            user_prompt: User message
            model: Model name (mimo-v2.5, mimo-v2.5-reasoning, mimo-v2.5-multimodal)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        session = await self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"MiMo API error {response.status}: {error_text}")

                if stream:
                    return await self._handle_stream(response)
                else:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]

        except aiohttp.ClientError as e:
            logger.error(f"MiMo API request failed: {e}")
            raise

    async def _handle_stream(self, response: aiohttp.ClientResponse) -> str:
        """Handle streaming response"""
        content = ""
        async for line in response.content:
            line = line.decode("utf-8").strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    content += delta
                except (json.JSONDecodeError, KeyError):
                    continue
        return content

    async def generate_image(self, 
                              prompt: str,
                              size: str = "1024x1024",
                              quality: str = "standard",
                              n: int = 1) -> Dict[str, Any]:
        """
        Generate image using MiMo image model

        Args:
            prompt: Image description
            size: Image size (1024x1024, 1536x1536, etc.)
            quality: Image quality (standard, hd)
            n: Number of images
        """
        payload = {
            "model": "mimo-image-v2",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }

        session = await self._get_session()

        async with session.post(
            f"{self.base_url}/images/generations",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"MiMo Image API error {response.status}: {error_text}")

            return await response.json()

    async def text_to_speech(self,
                              text: str,
                              voice: str = "zh-CN-XiaoxiaoNeural",
                              model: str = "mimo-tts-v1",
                              speed: float = 1.0,
                              response_format: str = "mp3") -> bytes:
        """
        Convert text to speech using MiMo TTS

        Args:
            text: Text to synthesize
            voice: Voice ID
            model: TTS model
            speed: Speech speed
            response_format: Audio format
        """
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": response_format
        }

        session = await self._get_session()

        async with session.post(
            f"{self.base_url}/audio/speech",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"MiMo TTS API error {response.status}: {error_text}")

            return await response.read()

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

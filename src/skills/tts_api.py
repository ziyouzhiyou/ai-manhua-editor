"""
Text-to-Speech API Wrapper
Supports multiple providers: MiMo, Azure, ElevenLabs
"""
import logging
import os
from typing import Dict, Any, Optional
import aiohttp

from src.skills.mimo_api import MiMoAPI

logger = logging.getLogger(__name__)


class TTSAPI:
    """
    Unified text-to-speech API
    """

    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("TTS_PROVIDER", "mimo")
        self.mimo_api = MiMoAPI()
        self.azure_key = os.getenv("AZURE_SPEECH_KEY", "")
        self.azure_region = os.getenv("AZURE_SPEECH_REGION", "eastasia")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")

    async def synthesize(self,
                          text: str,
                          voice_id: str = "zh-CN-XiaoxiaoNeural",
                          emotion: str = "neutral",
                          speed: float = 1.0,
                          language: str = "zh",
                          style: str = "natural") -> Any:
        """
        Synthesize speech

        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            emotion: Emotional tone
            speed: Speech speed
            language: Language code
            style: Voice style
        """
        if self.provider == "mimo":
            return await self._synthesize_mimo(text, voice_id, speed)
        elif self.provider == "azure":
            return await self._synthesize_azure(text, voice_id, emotion, speed)
        elif self.provider == "elevenlabs":
            return await self._synthesize_elevenlabs(text, voice_id, emotion)
        else:
            raise ValueError(f"Unknown TTS provider: {self.provider}")

    async def _synthesize_mimo(self, text: str, voice_id: str, speed: float) -> bytes:
        """Synthesize using MiMo TTS"""
        return await self.mimo_api.text_to_speech(
            text=text,
            voice=voice_id,
            speed=speed
        )

    async def _synthesize_azure(self, text: str, voice_id: str, emotion: str, speed: float) -> bytes:
        """Synthesize using Azure Speech API"""
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
            xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
            <voice name="{voice_id}">
                <mstts:express-as style="{emotion}">
                    <prosody rate="{int((speed - 1) * 100)}%">{text}</prosody>
                </mstts:express-as>
            </voice>
        </speak>"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://{self.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1",
                headers={
                    "Ocp-Apim-Subscription-Key": self.azure_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
                },
                data=ssml.encode("utf-8")
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Azure TTS error: {response.status}")
                return await response.read()

    async def _synthesize_elevenlabs(self, text: str, voice_id: str, emotion: str) -> bytes:
        """Synthesize using ElevenLabs API"""
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5 if emotion != "neutral" else 0.0
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.elevenlabs_key,
                    "Content-Type": "application/json"
                },
                json=payload
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"ElevenLabs error: {response.status}")
                return await response.read()

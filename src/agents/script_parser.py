"""
Script Parser Agent
Uses LLM to parse raw text/scripts into structured scene data
Optimized for Xiaomi MiMo API integration
"""
import json
import logging
import re
from typing import Dict, Any, List
from dataclasses import asdict

from src.models.schemas import Character, Scene, Dialogue, SceneType, CharacterGender, VoiceEmotion
from src.skills.mimo_api import MiMoAPI

logger = logging.getLogger(__name__)


class ScriptParserAgent:
    """
    Intelligent script parser that converts raw text into structured scenes
    Supports multiple input formats: plain text, screenplay format, novel format
    """

    def __init__(self, mimo_api: MiMoAPI = None):
        self.mimo_api = mimo_api or MiMoAPI()

    async def parse(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Parse script text into structured data

        Args:
            config: Task configuration
                - script_text: Raw script text
                - mode: "fast", "standard", or "deep"
                - language: "zh" or "en"
            context: Workflow context
            task_id: Current task ID
        """
        script_text = config.get("script_text", "")
        mode = config.get("mode", "standard")
        language = config.get("language", "zh")

        if not script_text:
            raise ValueError("No script text provided")

        logger.info(f"Parsing script (mode={mode}, length={len(script_text)} chars)")

        # Use MiMo API for intelligent parsing
        if mode == "deep":
            return await self._deep_parse(script_text, language, context)
        elif mode == "fast":
            return await self._fast_parse(script_text, language)
        else:
            return await self._standard_parse(script_text, language)

    async def _deep_parse(self, script_text: str, language: str, context: Dict) -> Dict[str, Any]:
        """Deep parsing with emotion analysis and character profiling"""

        system_prompt = """你是一个专业的AI漫剧剧本解析专家。请分析以下文本，提取：
1. 所有角色信息（姓名、性别、年龄、外貌特征、性格）
2. 场景列表（场景编号、类型、场景描述、时间、地点、氛围）
3. 每个场景中的对话（说话人、台词、情感、语速）
4. 动作描述和镜头指示
5. 情感基调分析

请严格按照JSON格式输出，确保结构完整。"""

        user_prompt = f"请解析以下剧本文本：

{script_text}

请输出完整的结构化数据。"

        response = await self.mimo_api.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="mimo-v2.5-reasoning",
            temperature=0.3,
            max_tokens=8000
        )

        try:
            parsed_data = self._extract_json(response)
            return self._normalize_parsed_data(parsed_data)
        except Exception as e:
            logger.error(f"Deep parse failed, falling back to standard: {e}")
            return await self._standard_parse(script_text, language)

    async def _standard_parse(self, script_text: str, language: str) -> Dict[str, Any]:
        """Standard parsing with structured extraction"""

        system_prompt = """You are a professional script parser for AI comic drama production.
Extract the following from the provided text:
1. Characters: name, gender, description
2. Scenes: scene number, type (dialogue/action/narration), setting, mood
3. Dialogues: speaker, text, emotion
4. Action descriptions

Output as valid JSON."""

        user_prompt = f"Parse this script:

{script_text}"

        response = await self.mimo_api.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="mimo-v2.5",
            temperature=0.2,
            max_tokens=6000
        )

        try:
            parsed_data = self._extract_json(response)
            return self._normalize_parsed_data(parsed_data)
        except Exception as e:
            logger.error(f"Standard parse failed, falling back to fast: {e}")
            return await self._fast_parse(script_text, language)

    async def _fast_parse(self, script_text: str, language: str) -> Dict[str, Any]:
        """Fast rule-based parsing"""
        characters = self._extract_characters_fast(script_text)
        scenes = self._extract_scenes_fast(script_text)

        return {
            "characters": [c.to_dict() for c in characters],
            "scenes": [s.to_dict() for s in scenes],
            "metadata": {
                "parse_mode": "fast",
                "character_count": len(characters),
                "scene_count": len(scenes),
                "language": language
            }
        }

    def _extract_characters_fast(self, text: str) -> List[Character]:
        """Fast character extraction using regex patterns"""
        characters = []
        seen_names = set()

        # Pattern for Chinese names (2-4 characters)
        cn_pattern = r'[一-鿿]{2,4}(?=[:：，,。！!？?])'
        # Pattern for "Name said/says"
        said_pattern = r'([A-Za-z一-鿿\s]{2,20})(?:说|道|喊道|问道|回答|said|said that)'

        for pattern in [cn_pattern, said_pattern]:
            matches = re.findall(pattern, text)
            for name in matches:
                name = name.strip()
                if name and name not in seen_names and len(name) >= 2:
                    seen_names.add(name)
                    gender = self._infer_gender(name)
                    characters.append(Character(
                        id=f"char_{len(characters)}",
                        name=name,
                        gender=gender
                    ))

        return characters

    def _extract_scenes_fast(self, text: str) -> List[Scene]:
        """Fast scene extraction"""
        scenes = []

        # Split by scene markers
        scene_markers = [
            r'第[一二三四五六七八九十\d]+[章节幕]',
            r'Scene \d+',
            r'===+',
            r'---+'
        ]

        combined_pattern = '|'.join(f'({m})' for m in scene_markers)
        parts = re.split(combined_pattern, text)

        scene_num = 1
        for i, part in enumerate(parts):
            if not part or len(part.strip()) < 50:
                continue

            scene = Scene(
                id=f"scene_{scene_num}",
                scene_number=scene_num,
                scene_type=SceneType.DIALOGUE,
                description=part[:200],
                dialogues=self._extract_dialogues_fast(part)
            )
            scenes.append(scene)
            scene_num += 1

        if not scenes:
            # Create single scene if no markers found
            scenes.append(Scene(
                id="scene_1",
                scene_number=1,
                scene_type=SceneType.DIALOGUE,
                description=text[:200],
                dialogues=self._extract_dialogues_fast(text)
            ))

        return scenes

    def _extract_dialogues_fast(self, text: str) -> List[Dialogue]:
        """Extract dialogues from text"""
        dialogues = []

        # Pattern: "Name: dialogue" or "Name said: dialogue"
        patterns = [
            r'([一-鿿]{2,4})[：:]([^
]+)',
            r'"([^"]+)"[\s]*[-—]\s*([一-鿿]{2,4})',
            r'([一-鿿]{2,4})(?:说|道)[：:]([^
]+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    speaker, line = match
                else:
                    line, speaker = match

                dialogues.append(Dialogue(
                    character_id=speaker.strip(),
                    text=line.strip(),
                    emotion=self._infer_emotion(line)
                ))

        return dialogues

    def _infer_gender(self, name: str) -> CharacterGender:
        """Infer character gender from name"""
        # Simple heuristic for Chinese names
        female_indicators = ['芳', '娜', '丽', '婷', '娟', '敏', '静', '秀', '玲', '燕', '梅', '兰', '红', '英', '华', '云', '霞', '雪', '月', '花']
        male_indicators = ['伟', '强', '军', '杰', '勇', '磊', '明', '涛', '超', '俊', '峰', '建', '浩', '宇', '鑫', '博', '文', '武', '刚', '毅']

        for char in name:
            if char in female_indicators:
                return CharacterGender.FEMALE
            if char in male_indicators:
                return CharacterGender.MALE

        return CharacterGender.UNKNOWN

    def _infer_emotion(self, text: str) -> VoiceEmotion:
        """Infer emotion from text"""
        emotion_keywords = {
            VoiceEmotion.HAPPY: ['开心', '高兴', '笑', '哈哈', '棒', '太好了', 'happy', 'glad', 'laugh'],
            VoiceEmotion.SAD: ['伤心', '难过', '哭', '泪', '悲伤', 'sad', 'cry', 'tear'],
            VoiceEmotion.ANGRY: ['生气', '愤怒', '恨', '可恶', 'angry', 'mad', 'hate'],
            VoiceEmotion.EXCITED: ['兴奋', '激动', '哇', '太棒了', 'excited', 'wow', 'amazing'],
            VoiceEmotion.SCARED: ['害怕', '恐惧', '吓', '怕', 'scared', 'afraid', 'fear'],
            VoiceEmotion.ROMANTIC: ['爱', '喜欢', '心动', '浪漫', 'love', 'like', 'romantic']
        }

        text_lower = text.lower()
        for emotion, keywords in emotion_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    return emotion

        return VoiceEmotion.NEUTRAL

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        raise ValueError("No JSON found in response")

    def _normalize_parsed_data(self, data: Dict) -> Dict[str, Any]:
        """Normalize parsed data to standard format"""
        characters = []
        for char_data in data.get("characters", []):
            gender = CharacterGender(char_data.get("gender", "unknown").lower())
            characters.append(Character(
                id=char_data.get("id", f"char_{len(characters)}"),
                name=char_data.get("name", "Unknown"),
                gender=gender,
                age=char_data.get("age"),
                description=char_data.get("description", ""),
                personality=char_data.get("personality", ""),
                appearance=char_data.get("appearance", "")
            ))

        scenes = []
        for scene_data in data.get("scenes", []):
            scene_type = SceneType(scene_data.get("scene_type", "dialogue").lower())
            dialogues = []
            for d in scene_data.get("dialogues", []):
                dialogues.append(Dialogue(
                    character_id=d.get("character_id", ""),
                    text=d.get("text", ""),
                    emotion=VoiceEmotion(d.get("emotion", "neutral").lower())
                ))

            scenes.append(Scene(
                id=scene_data.get("id", f"scene_{len(scenes)}"),
                scene_number=scene_data.get("scene_number", len(scenes) + 1),
                scene_type=scene_type,
                title=scene_data.get("title", ""),
                description=scene_data.get("description", ""),
                setting=scene_data.get("setting", ""),
                time_of_day=scene_data.get("time_of_day", ""),
                mood=scene_data.get("mood", ""),
                characters=scene_data.get("characters", []),
                dialogues=dialogues,
                action_description=scene_data.get("action_description", ""),
                camera_direction=scene_data.get("camera_direction", ""),
                lighting=scene_data.get("lighting", "")
            ))

        return {
            "characters": [c.to_dict() for c in characters],
            "scenes": [s.to_dict() for s in scenes],
            "metadata": {
                "parse_mode": "llm",
                "character_count": len(characters),
                "scene_count": len(scenes),
                "source": "mimo_api"
            }
        }

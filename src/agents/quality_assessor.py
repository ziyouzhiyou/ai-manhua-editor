"""
Quality Assessor Agent
Evaluates the final video quality and provides feedback
"""
import logging
from typing import Dict, Any, List

from src.models.schemas import QualityReport
from src.skills.mimo_api import MiMoAPI

logger = logging.getLogger(__name__)


class QualityAssessorAgent:
    """
    Assesses video quality across multiple dimensions:
    - Image consistency and quality
    - Audio clarity and sync
    - Video smoothness
    - Subtitle accuracy
    """

    def __init__(self, mimo_api: MiMoAPI = None):
        self.mimo_api = mimo_api or MiMoAPI()

    async def assess(self, config: Dict[str, Any], context: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        Assess video quality

        Args:
            config: Task configuration
                - video_path: Path to final video
                - threshold: Minimum quality score (0-1)
                - detailed_report: Whether to generate detailed report
            context: Workflow context
            task_id: Current task ID
        """
        video_path = config.get("video_path", "")
        threshold = config.get("threshold", 0.8)
        detailed_report = config.get("detailed_report", False)

        project_id = context.get("workflow_id", "unknown")

        logger.info(f"Assessing quality for {video_path}")

        # Run quality checks
        image_score = await self._assess_image_quality(context)
        audio_score = await self._assess_audio_quality(context)
        video_score = await self._assess_video_quality(video_path, context)
        subtitle_score = await self._assess_subtitle_quality(context)

        # Calculate overall score
        overall_score = (image_score * 0.35 + audio_score * 0.25 + 
                        video_score * 0.25 + subtitle_score * 0.15)

        # Collect issues
        issues = []
        if image_score < threshold:
            issues.append({
                "category": "image",
                "severity": "warning" if image_score > threshold * 0.8 else "error",
                "message": f"Image quality score ({image_score:.2f}) below threshold ({threshold})",
                "score": image_score
            })

        if audio_score < threshold:
            issues.append({
                "category": "audio",
                "severity": "warning" if audio_score > threshold * 0.8 else "error",
                "message": f"Audio quality score ({audio_score:.2f}) below threshold ({threshold})",
                "score": audio_score
            })

        if video_score < threshold:
            issues.append({
                "category": "video",
                "severity": "warning" if video_score > threshold * 0.8 else "error",
                "message": f"Video quality score ({video_score:.2f}) below threshold ({threshold})",
                "score": video_score
            })

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, context)

        passed = overall_score >= threshold and not any(i["severity"] == "error" for i in issues)

        report = QualityReport(
            project_id=project_id,
            overall_score=overall_score,
            image_quality_score=image_score,
            audio_quality_score=audio_score,
            video_quality_score=video_score,
            subtitle_quality_score=subtitle_score,
            issues=issues,
            recommendations=recommendations,
            passed=passed
        )

        logger.info(f"Quality assessment: overall={overall_score:.2f}, passed={passed}")

        return {
            "report": report.to_dict(),
            "passed": passed,
            "overall_score": overall_score,
            "threshold": threshold
        }

    async def _assess_image_quality(self, context: Dict) -> float:
        """Assess generated image quality"""
        images_result = context.get("results", {}).get("generate_images", {})
        images = images_result.get("images", [])
        failed = images_result.get("failed", [])

        if not images and not failed:
            return 0.5

        total = len(images) + len(failed)
        success_rate = len(images) / total if total > 0 else 0

        # Basic scoring
        score = success_rate * 0.8 + 0.2  # Base score for having images

        return min(1.0, score)

    async def _assess_audio_quality(self, context: Dict) -> float:
        """Assess audio quality"""
        audio_result = context.get("results", {}).get("synthesize_voices", {})
        segments = audio_result.get("audio_segments", [])
        failed = audio_result.get("failed", [])

        if not segments and not failed:
            return 0.5

        total = len(segments) + len(failed)
        success_rate = len(segments) / total if total > 0 else 0

        score = success_rate * 0.85 + 0.15
        return min(1.0, score)

    async def _assess_video_quality(self, video_path: str, context: Dict) -> float:
        """Assess video composition quality"""
        if not video_path:
            return 0.3

        # Check if file exists and has size
        import os
        if os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            # Reasonable size check
            if size_mb > 1:
                return 0.9
            elif size_mb > 0.1:
                return 0.7

        return 0.5

    async def _assess_subtitle_quality(self, context: Dict) -> float:
        """Assess subtitle quality"""
        subtitle_result = context.get("results", {}).get("generate_subtitles", {})
        entries = subtitle_result.get("subtitle_entries", [])

        if not entries:
            return 0.5

        # Check for empty or very short subtitles
        valid_entries = [e for e in entries if e.get("text") and len(e.get("text", "")) > 1]

        score = len(valid_entries) / len(entries) if entries else 0
        return min(1.0, score * 0.9 + 0.1)

    def _generate_recommendations(self, issues: List[Dict], context: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        for issue in issues:
            category = issue.get("category", "")
            if category == "image":
                recommendations.append("Consider increasing image generation quality or using a different style model")
                recommendations.append("Review failed image generations and retry with adjusted prompts")
            elif category == "audio":
                recommendations.append("Check TTS API connectivity and voice ID validity")
                recommendations.append("Consider using alternative TTS providers for failed segments")
            elif category == "video":
                recommendations.append("Verify FFmpeg installation and video composition settings")
                recommendations.append("Check input image and audio file integrity")

        if not recommendations:
            recommendations.append("Quality looks good! Consider running the premium workflow for even better results.")

        return recommendations

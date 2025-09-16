from typing import List, Dict, Any
import json
import os
from datetime import datetime
from ..models.content_models import ContentRequest, ContentDraft, QualityReport


class ContentHistory:
    def __init__(self, storage_path: str = "data/content_history.json"):
        self.storage_path = storage_path
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load content history from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return []

    def save_content_session(
        self,
        request: ContentRequest,
        draft: ContentDraft,
        quality_report: QualityReport,
        approved: bool = False,
    ):
        """Save a complete content creation session"""
        session = {
            "timestamp": datetime.now().isoformat(),
            "request": request.model_dump(),
            "draft": draft.model_dump(),
            "quality_report": quality_report.model_dump(),
            "approved": approved,
            "feedback": None,
        }

        self.history.append(session)
        self._save_history()

    def add_feedback(self, request_id: str, feedback: Dict[str, Any]):
        """Add feedback to a content session"""
        for session in self.history:
            if session["draft"]["request_id"] == request_id:
                session["feedback"] = feedback
                session["feedback"]["timestamp"] = datetime.now().isoformat()
                break

        self._save_history()

    def get_successful_content(self, content_type: str = None) -> List[Dict[str, Any]]:
        """Get previously successful content for learning"""
        successful = []
        for session in self.history:
            if (
                session.get("approved", False)
                and session["quality_report"]["overall_score"] >= 80
            ):

                if (
                    content_type is None
                    or session["request"]["content_type"] == content_type
                ):
                    successful.append(session)

        return successful[-10:]  # Return last 10 successful pieces

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        if not self.history:
            return {}

        total_content = len(self.history)
        approved_content = sum(1 for s in self.history if s.get("approved", False))
        avg_quality_score = (
            sum(s["quality_report"]["overall_score"] for s in self.history)
            / total_content
        )

        return {
            "total_content_pieces": total_content,
            "approval_rate": (
                approved_content / total_content if total_content > 0 else 0
            ),
            "average_quality_score": avg_quality_score,
            "content_types": {},  # Could add breakdown by content type
        }

    def _save_history(self):
        """Save history to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.history, f, indent=2)

from typing import Dict, Any, List
import json
import os


class UserPreferences:
    def __init__(self, storage_path: str = "data/user_preferences.json"):
        self.storage_path = storage_path
        self.preferences = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except:
                pass

        return {
            "default_tone": "professional",
            "preferred_length": "medium",
            "content_types": [],
            "target_audiences": [],
            "writing_style_notes": "",
            "favorite_topics": [],
            "content_goals": [],
        }

    def save_preferences(self):
        """Save preferences to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.preferences, f, indent=2)

    def update_preference(self, key: str, value: Any):
        """Update a specific preference"""
        self.preferences[key] = value
        self.save_preferences()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a specific preference"""
        return self.preferences.get(key, default)

    def learn_from_feedback(self, content_type: str, feedback: Dict[str, Any]):
        """Learn from content feedback to update preferences"""
        if feedback.get("approved", False):
            # Learn from successful content
            if "tone" in feedback:
                self.preferences["successful_tones"] = self.preferences.get(
                    "successful_tones", []
                )
                self.preferences["successful_tones"].append(feedback["tone"])

        self.save_preferences()

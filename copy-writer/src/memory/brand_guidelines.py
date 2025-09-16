from typing import Dict, Any
import json
import os


class BrandGuidelines:
    def __init__(self, storage_path: str = "data/brand_guidelines.json"):
        self.storage_path = storage_path
        self.guidelines = self._load_guidelines()

    def _load_guidelines(self) -> Dict[str, Any]:
        """Load brand guidelines from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except:
                pass

        return {
            "brand_voice": "Professional, helpful, and authentic",
            "tone_guidelines": {
                "professional": "Clear, authoritative, informative",
                "casual": "Friendly, conversational, approachable",
                "technical": "Precise, detailed, educational",
            },
            "writing_style": {
                "sentence_length": "Mix of short and medium sentences",
                "paragraph_length": "3-5 sentences maximum",
                "use_active_voice": True,
                "avoid_jargon": True,
            },
            "brand_values": [],
            "messaging_pillars": [],
            "do_not_use": [],
            "preferred_terms": {},
        }

    def get_guidelines(self) -> str:
        """Get formatted brand guidelines for prompts"""
        guidelines_text = f"""
        Brand Voice: {self.guidelines['brand_voice']}
        
        Writing Style:
        - Sentence length: {self.guidelines['writing_style']['sentence_length']}
        - Paragraph length: {self.guidelines['writing_style']['paragraph_length']}
        - Use active voice: {self.guidelines['writing_style']['use_active_voice']}
        - Avoid jargon: {self.guidelines['writing_style']['avoid_jargon']}
        """

        if self.guidelines["brand_values"]:
            guidelines_text += (
                f"\nBrand Values: {', '.join(self.guidelines['brand_values'])}"
            )

        if self.guidelines["do_not_use"]:
            guidelines_text += (
                f"\nAvoid using: {', '.join(self.guidelines['do_not_use'])}"
            )

        return guidelines_text.strip()

    def update_guidelines(self, updates: Dict[str, Any]):
        """Update brand guidelines"""
        self.guidelines.update(updates)
        self._save_guidelines()

    def _save_guidelines(self):
        """Save guidelines to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.guidelines, f, indent=2)

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: Optional[str] = "https://api.openai.com/v1"  # Default OpenAI URL
    openai_model: Optional[str] = "gpt-4"

    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "content-writer-agent"

    # Content settings
    default_tone: str = "professional"
    default_length: str = "medium"  # short, medium, long
    max_content_length: int = 1200

    # SEO settings
    target_keyword_density: float = 0.02  # 2%
    min_readability_score: int = 60

    class Config:
        env_file = ".env"

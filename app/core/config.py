"""Application configuration module"""

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM API configuration"""

    # OpenAI configuration
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None

    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 4000

    def __post_init__(self):
        # Load from environment variables if not provided
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_base_url:
            self.openai_base_url = os.getenv("OPENAI_BASE_URL")

    @property
    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return bool(self.openai_api_key)


# Global config instance
llm_config = LLMConfig()

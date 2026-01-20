"""
Configuration management for the exam system.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    # Together.ai API configuration
    together_api_key: str = "317bc321df4bc7a51f97d8b4324d35cf8d0b168d27a714228c21aa1e8b7ed8e7"
    together_api_url: str = "https://api.together.xyz/v1/chat/completions"
    together_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # Default serverless model
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Exam configuration
    default_domain: str = "Computer Science"
    default_professor_instructions: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

from pathlib import Path
import os
import yaml
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class LLMConfig(BaseModel):
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 2048


class EmbeddingConfig(BaseModel):
    model_name: str = "openai:text-embedding-3-small"


class ChunkingConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200


class RetrieverConfig(BaseModel):
    top_k: int = 4
    search_type: str = "similarity"


class StorageConfig(BaseModel):
    collection_name: str = "stock_embeddings"


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retriever: RetrieverConfig = Field(default_factory=RetrieverConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Loads configuration from YAML file and applies any environment variable overrides.
    """
    path = config_path or DEFAULT_CONFIG_PATH
    data = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    cfg = AppConfig(**data)

    # Optional Environment variable overrides
    env_provider = os.environ.get("LLM_PROVIDER")
    if env_provider:
        cfg.llm.provider = env_provider

    env_model = os.environ.get("BEDROCK_MODEL_ID") or os.environ.get("LLM_MODEL_NAME")
    if env_model:
        cfg.llm.model_name = env_model

    env_embed = os.environ.get("EMBEDDING_MODEL_NAME")
    if env_embed:
        cfg.embeddings.model_name = env_embed

    return cfg


# Global singleton configuration object
config = load_config()

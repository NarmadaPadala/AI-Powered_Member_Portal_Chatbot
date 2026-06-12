import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _get_secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        secret_value = st.secrets.get(name, default)
        return str(secret_value) if secret_value is not None else default
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    pinecone_api_key: str
    index_name: str = "healthcare-support-rag"
    cloud: str = "aws"
    region: str = "us-east-1"
    namespace: str = "demo-healthcare-support"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4.1-mini"
    embedding_dimension: int = 512


def get_settings(require_api_key: bool = True) -> Settings:
    openai_api_key = _get_secret("OPENAI_API_KEY")
    pinecone_api_key = _get_secret("PINECONE_API_KEY")
    if require_api_key and (not openai_api_key or not pinecone_api_key):
        raise RuntimeError(
            "OPENAI_API_KEY and PINECONE_API_KEY are required. "
            "Copy .env.demo to .env and add your credentials."
        )

    return Settings(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        index_name=_get_secret("PINECONE_INDEX_NAME", "healthcare-support-rag"),
        cloud=_get_secret("PINECONE_CLOUD", "aws"),
        region=_get_secret("PINECONE_REGION", "us-east-1"),
        namespace=_get_secret("PINECONE_NAMESPACE", "demo-healthcare-support"),
        embedding_model=_get_secret("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=_get_secret("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        embedding_dimension=int(_get_secret("PINECONE_DIMENSION", "512")),
    )

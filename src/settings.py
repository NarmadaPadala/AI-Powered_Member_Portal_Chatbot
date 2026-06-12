import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


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
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
    if require_api_key and (not openai_api_key or not pinecone_api_key):
        raise RuntimeError(
            "OPENAI_API_KEY and PINECONE_API_KEY are required. "
            "Copy .env.demo to .env and add your credentials."
        )

    return Settings(
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        index_name=os.getenv("PINECONE_INDEX_NAME", "healthcare-support-rag"),
        cloud=os.getenv("PINECONE_CLOUD", "aws"),
        region=os.getenv("PINECONE_REGION", "us-east-1"),
        namespace=os.getenv("PINECONE_NAMESPACE", "demo-healthcare-support"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        embedding_dimension=int(os.getenv("PINECONE_DIMENSION", "512")),
    )

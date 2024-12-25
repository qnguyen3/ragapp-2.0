from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RAG API"
    PORT: int = 3456
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Databases
    CHROMA_DB_PATH: str = "./data/chroma_db"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ragapp"
    
    # Models
    EMBEDDING_MODEL: str = "ibm-granite/granite-embedding-278m-multilingual"
    MLX_MODEL: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    MLX_URL: str = "http://localhost:8000/v1"
    CHUNK_SIZE: int = 512
    MAX_CONTEXT_CHUNKS: int = 10  # Number of relevant chunks to use for context
    MAX_CHAT_HISTORY: int = 5    # Number of previous chat turns to include
    
    # Collection
    COLLECTION_NAME: str = "documents"
    
    class Config:
        env_file = ".env"

settings = Settings()

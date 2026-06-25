from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql://testgen:testgen_secret@localhost:5432/testgen_db"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "java_code_chunks"

    # OpenAI
    openai_api_key: str = ""
    openai_api_base: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o"

    # Mistral
    mistral_api_key: str = ""
    mistral_api_base: str | None = None
    mistral_chat_model: str = "mistral-small-latest"
    mistral_embedding_model: str = "mistral-embed"
    # Properties for unified LLM access
    @property
    def effective_api_key(self) -> str:
        return self.openai_api_key or self.mistral_api_key
    @property
    def effective_api_base(self) -> str | None:
        base = self.openai_api_base or self.mistral_api_base
        if base and base.endswith("/"):
            base = base[:-1]
        return base
    @property
    def effective_chat_model(self) -> str:
        return self.openai_chat_model if self.openai_api_key else self.mistral_chat_model
    @property
    def effective_embedding_model(self) -> str:
        return self.openai_embedding_model if self.openai_api_key else self.mistral_embedding_model

    # JWT
    secret_key: str = "change-me-in-production-at-least-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Java
    java_parser_jar: str = "/app/java-parser/target/analyzer-cli-1.0.0.jar"
    jdk_home: str = "/usr/lib/jvm/default-java"

    # App
    debug: bool = False
    app_env: str = "production"
    max_upload_size_mb: int = 50
    upload_dir: str = "/app/uploads"
    results_dir: str = "/app/results"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

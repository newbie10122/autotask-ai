from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_session_secret: str = "development-only"
    app_session_ttl_seconds: int = 28800
    app_route_auth_required: bool = False
    auth_login_failure_limit: int = 5
    auth_login_failure_window_seconds: int = 300
    database_url: str = "postgresql://autotask_ai:change-me@postgres:5432/autotask_ai"
    redis_url: str = "redis://redis:6379/0"
    autotask_base_url: str = "https://webservices.autotask.net/atservicesrest"
    autotask_username: str = ""
    autotask_secret: str = ""
    autotask_api_integration_code: str = ""
    autotask_page_size: int = 500
    autotask_sync_batch_limit: int = 500
    ollama_base_url: str = "http://ollama:11434"
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_batch_size: int = 16
    embed_noise_chunks: bool = False
    answer_target_seconds: int = 20
    assistant_normal_timeout_seconds: int = 90
    assistant_max_context_chunks: int = 8
    assistant_max_unique_tickets: int = 5
    assistant_max_chunks_per_ticket: int = 2
    assistant_exclude_noise_by_default: bool = True
    deep_dive_timeout_seconds: int = 120
    operations_status_cache_ttl_seconds: int = 30
    ticket_health_summary_cache_ttl_seconds: int = 60
    customer_success_summary_cache_ttl_seconds: int = 60


settings = Settings()

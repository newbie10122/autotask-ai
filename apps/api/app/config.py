from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_session_secret: str = "development-only"
    database_url: str = "postgresql://autotask_ai:change-me@postgres:5432/autotask_ai"
    autotask_base_url: str = "https://webservices.autotask.net/atservicesrest"
    autotask_username: str = ""
    autotask_secret: str = ""
    autotask_api_integration_code: str = ""
    autotask_page_size: int = 500
    answer_target_seconds: int = 20


settings = Settings()


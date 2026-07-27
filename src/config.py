from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    resend_api_key: str
    resend_from_email: str = "alerts@visapolicy.ai"
    federal_register_base_url: str = "https://www.federalregister.gov/api/v1"
    lookback_days: int = 7
    frontend_base_url: str = "http://localhost:3000"
    jwt_secret_key: str

    model_config = {"env_file": ".env"}


settings = Settings()

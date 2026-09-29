from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_host: str = "http://localhost:11434"
    planner_model: str = "llama3.1:8b"
    agent_model: str = "llama3.1:8b"
    workspace_dir: str = "workspace"
    max_subtasks: int = 12


settings = Settings()
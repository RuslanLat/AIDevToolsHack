from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class LlmСonfig(ConfigBase):
    LLM_MODEL: str
    LLM_API_BASE: str
    LLM_API_KEY: str


class McpСonfig(ConfigBase):
    MCP_SERVER_URL: str
    MCP_API_KEY: str


class Config(BaseSettings):
    llm: LlmСonfig = Field(default_factory=LlmСonfig)
    mcp: McpСonfig = Field(default_factory=McpСonfig)

    @classmethod
    def load(cls) -> "Config":
        return cls()

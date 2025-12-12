from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class EmailСonfig(ConfigBase):
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    SMTP_HOST: str
    SMTP_PORT: int
    IMAP_HOST: str
    IMAP_PORT: int


class CalDavСonfig(ConfigBase):
    CALDAV_URL: str
    CALDAV_USERNAME: str
    CALDAV_PASSWORD: str
    CALDAV_CALENDAR_NAME: str


class McpServerConfig(ConfigBase):
    MCP_HOST: str
    MCP_PORT: int


class Config(BaseSettings):
    mcp: McpServerConfig = Field(default_factory=McpServerConfig)
    email: EmailСonfig = Field(default_factory=EmailСonfig)
    cal_dav: CalDavСonfig = Field(default_factory=CalDavСonfig)

    @classmethod
    def load(cls) -> "Config":
        return cls()

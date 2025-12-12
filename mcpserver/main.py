from fastmcp import FastMCP

from src.core.email import create_email_module
from src.core.calendar import create_calendar_module
from src.config import Config


config = Config.load()


def create_app() -> FastMCP:
    mcp = FastMCP("UnifiedEmailCalendarMCP")
    mcp.mount(create_email_module(), prefix="email")
    mcp.mount(create_calendar_module(), prefix="calendar")
    return mcp


if __name__ == "__main__":
    mcp = create_app()
    mcp.run(
        transport="http",
        host=config.mcp.MCP_HOST,
        port=config.mcp.MCP_PORT,
    )

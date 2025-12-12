from fastmcp import FastMCP

from src.config import Config
from .prompts import setup_prompts
from .resources import setup_resources
from .tools import setup_tools
from .utils import (
    _send_raw_email,
    _fetch_emails,
    _decode_mime_words,
    _clean_email_body,
)


def create_email_module() -> FastMCP:
    mcp = FastMCP("EmailModule")
    config = Config.load()

    setup_tools(
        mcp,
        config,
        _send_raw_email,
        _fetch_emails,
        _decode_mime_words,
        _clean_email_body,
    )
    setup_resources(mcp, config, _decode_mime_words)
    setup_prompts(mcp)

    return mcp

# src/core/calendar/__init__.py

import aiocaldav
from aiocaldav import Calendar
from src.config import Config
from fastmcp import FastMCP

from .prompts import setup_prompts
from .resources import setup_resources
from .tools import setup_tools

_client = None
_calendar = None
config = Config.load()


async def _get_calendar():
    "получение календаря"
    global _client, _calendar
    if _calendar:
        return _calendar
    if not all(
        [
            config.cal_dav.CALDAV_URL,
            config.cal_dav.CALDAV_USERNAME,
            config.cal_dav.CALDAV_PASSWORD,
        ]
    ):
        raise RuntimeError("CalDAV not configured")

    _client = aiocaldav.DAVClient(
        url=config.cal_dav.CALDAV_URL,
        username=config.cal_dav.CALDAV_USERNAME,
        password=config.cal_dav.CALDAV_PASSWORD,
    )
    principal = await _client.principal()
    calendars: list[Calendar] = await principal.calendars()
    if not calendars:
        raise RuntimeError("No calendars found")

    for cal in calendars:
        name = cal.name
        if name == config.cal_dav.CALDAV_CALENDAR_NAME:
            _calendar = cal
            return cal
    _calendar = calendars[0]
    return _calendar


def create_calendar_module() -> FastMCP:
    mcp = FastMCP("CalendarModule")

    setup_tools(mcp, _get_calendar)
    setup_resources(mcp, _get_calendar)
    setup_prompts(mcp)

    return mcp

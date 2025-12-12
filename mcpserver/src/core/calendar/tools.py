import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Optional

import vobject
from aiocaldav import Event
from fastmcp import FastMCP


def setup_tools(mcp: FastMCP, _get_calendar: callable):
    @mcp.tool
    async def create_calendar_event(
        summary: str,
        start: str,
        end: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """
        Создать новое событие в календаре.
        Формат даты/времени: ISO 8601 (например, "2025-12-05T10:00:00").
        """
        cal = await _get_calendar()
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        vevent = vobject.iCalendar()
        vevent.add("vevent")
        vevent.vevent.add("uid").value = str(uuid.uuid4())
        vevent.vevent.add("summary").value = summary
        vevent.vevent.add("dtstart").value = start_dt
        vevent.vevent.add("dtend").value = end_dt
        if description:
            vevent.vevent.add("description").value = description
        if location:
            vevent.vevent.add("location").value = location
        await cal.add_event(vevent.serialize())
        return {"status": "event_created", "summary": summary}

    @mcp.tool
    async def list_calendar_events(
        start: str = None, end: str = None, limit: int = 10
    ) -> dict:
        """
        Получить список событий в заданном временном диапазоне.
        Если диапазон не указан — возвращает события за ближайшие 7 дней.
        """
        cal = await _get_calendar()
        msk_tz = timezone(timedelta(hours=3), name="MSK")
        now = datetime.now(msk_tz)
        start_dt = datetime.fromisoformat(start) if start else now
        end_dt = datetime.fromisoformat(end) if end else (now + timedelta(days=7))
        events: list[Event] = await cal.date_search(start_dt, end_dt)
        result = []
        for ev in events[:limit]:
            comp = ev.instance.vevent
            result.append(
                {
                    "uid": str(comp.uid.value),
                    "summary": comp.summary.value
                    if hasattr(comp.summary, "value")
                    else "",
                    "description": comp.description.value
                    if hasattr(comp, "description")
                    else "",
                    "location": comp.location.value
                    if hasattr(comp, "location")
                    else "",
                    "start": comp.dtstart.value.isoformat(),
                    "end": comp.dtend.value.isoformat(),
                }
            )
        return {"events": result}

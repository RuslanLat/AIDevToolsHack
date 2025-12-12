from datetime import (
    datetime,
    timedelta,
    timezone,
)

from fastmcp import (
    Context,
    FastMCP,
)


def setup_resources(mcp: FastMCP, _get_calendar: callable):
    @mcp.resource("events://today")
    async def get_todays_events(ctx: Context = None) -> dict:
        """
        Ресурс для автоматической загрузки всех событий на текущую дату.
        Используется агентом для понимания, какие встречи сегодня.
        """

        today = datetime.now().date()
        start_dt = datetime.combine(today, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)

        cal = await _get_calendar()
        events = await cal.date_search(start_dt, end_dt)
        today_events = []
        for ev in events:
            comp = ev.instance.vevent
            today_events.append(
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
                    "organizer": comp.organizer if hasattr(comp, "organizer") else "",
                    "start": comp.dtstart.value.isoformat(),
                    "end": comp.dtend.value.isoformat(),
                }
            )

        return {
            "description": f"События на {today.isoformat()}",
            "events": today_events,
        }

    # === РЕСУРС: calendar://next-hour ===
    @mcp.resource("calendar://next-hour")
    async def get_next_hour_event(ctx: Context = None) -> dict:
        """Возвращает ближайшее событие в течение следующего часа."""
        msk_tz = timezone(timedelta(hours=3), name="MSK")
        now = datetime.now(msk_tz)
        end = now + timedelta(hours=1)

        cal = await _get_calendar()
        events = await cal.date_search(now, end)
        if not events:
            return {"description": "Нет событий в ближайший час", "event": None}

        # Берём первое (самое ближайшее)
        ev = events[0]
        comp = ev.instance.vevent
        return {
            "description": "Ближайшее событие",
            "event": {
                "uid": str(comp.uid.value),
                "summary": comp.summary.value if hasattr(comp.summary, "value") else "",
                "description": comp.description.value
                if hasattr(comp, "description")
                else "",
                "location": comp.location.value if hasattr(comp, "location") else "",
                "start": comp.dtstart.value.isoformat(),
                "end": comp.dtend.value.isoformat(),
            },
        }

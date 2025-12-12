from fastmcp import (
    Context,
    FastMCP,
)


def setup_prompts(mcp: FastMCP):
    # === ПРОМПТ: generate_event_from_email ===

    @mcp.prompt(
        name="generate_event_from_email",
        description="""
        Создаёт промпт, который просит LLM сформулировать событие на основе email.
        Используется как шаблон для агента: "Прочитай письмо и создай событие, если нужно".
        """,
    )
    async def generate_event_from_email(
        email_from: str, email_subject: str, email_body: str, ctx: Context = None
    ) -> str:
        """
        Создаёт промпт, который просит LLM сформулировать событие на основе email.
        Используется как шаблон для агента: "Прочитай письмо и создай событие, если нужно".
        """
        return (
            f"На основе следующего письма сформулируй краткую задачу (to-do), "
            f"если ответ или действие требуется от получателя. Иначе верни 'NO_EVENT'.\n\n"
            f"Отправитель: {email_from}\n"
            f"Тема: {email_subject}\n"
            f"Текст:\n{email_body[:1000]}\n\n"
            f"Формат ответа: одна строка — краткое описание задачи (например, 'Ответить на запрос о MCP'), "
            f"или 'NO_EVENT', если действия не требуется."
        )

    # === ПРОМПТ: should_create_event_from_email ===

    @mcp.prompt
    async def should_create_enent_from_email(
        email_from: str, email_subject: str, email_body: str, ctx: Context = None
    ) -> str:
        return (
            f"Требует ли это письмо от вас какого-либо действия (ответ, задача, подтверждение)?\n"
            f"Отправитель: {email_from}\n"
            f"Тема: {email_subject}\n"
            f"Текст:\n{email_body[:800]}\n\n"
            f"Ответь только 'YES' или 'NO'."
        )

    # === ПРОМПТ: plan_day_from_calendar ===

    @mcp.prompt
    async def plan_day_from_calendar(ctx: Context = None) -> str:
        # Читаем сегодняшние события
        today_events = await ctx.read_resource("events://calendar/today")

        return (
            f"Составь краткий план дня на основе следующих данных:\n\n"
            f"События сегодня: {len(today_events.get('events', []))} шт.\n"
            f"Выведи структурированный план в формате:\n"
            f"- Утро: ...\n- День: ...\n- Вечер: ...\n"
            f"Или напиши 'Спокойный день', если нет срочных дел."
        )

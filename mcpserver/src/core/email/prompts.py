from fastmcp import (
    Context,
    FastMCP,
)


def setup_prompts(mcp: FastMCP):
    # === ПРОМПТ: summarize_inbox ===
    @mcp.prompt
    async def summarize_inbox(ctx: Context = None) -> str:
        """Генерирует промпт для сводки по входящим."""
        unread = await ctx.read_resource("emails://email/unread")
        email_list = [
            f"- {e['from']}: {e['subject']}" for e in unread.get("emails", [])
        ]
        if not email_list:
            email_list = ["Нет непрочитанных писем"]

        return (
            "Составь краткую (1–2 предложения) сводку по входящим письмам:\n"
            + "\n".join(email_list[:5])
        )

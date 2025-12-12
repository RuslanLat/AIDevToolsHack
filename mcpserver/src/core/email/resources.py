import aioimaplib
import email as email_lib
from fastmcp import (
    FastMCP,
    Context,
)

from src.config import Config


def setup_resources(mcp: FastMCP, config: Config, _decode_mime_words: callable):
    # === РЕСУРС: emails://unread ===
    @mcp.resource("emails://unread")
    async def get_unread_emails(ctx: Context = None) -> dict:
        """Возвращает последние 5 непрочитанных писем (если IMAP поддерживает \\Seen)."""
        client = aioimaplib.IMAP4_SSL(config.email.IMAP_HOST, config.email.IMAP_PORT)
        try:
            await client.wait_hello_from_server()
            await client.login(config.email.EMAIL_ADDRESS, config.email.EMAIL_PASSWORD)
            await client.select("INBOX")
            # Ищем непрочитанные: NOT SEEN
            _, data = await client.search("UNSEEN")
            email_ids = data[0].split()[-5:] if data[0] else []

            emails = []
            for uid in email_ids:
                uid_str = uid.decode("utf-8")
                _, msg_data = await client.fetch(uid_str, "(RFC822)")
                raw_header = msg_data[1]
                parsed = email_lib.message_from_bytes(raw_header)
                emails.append(
                    {
                        "from": _decode_mime_words(parsed.get("From", "")),
                        "subject": _decode_mime_words(
                            parsed.get("Subject", "(no subject)")
                        ),
                        "date": parsed.get("Date", ""),
                    }
                )
            return {"description": "Непрочитанные письма", "emails": emails}
        finally:
            await client.logout()

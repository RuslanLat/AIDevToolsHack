import email as email_lib
from typing import (
    List,
    Optional,
)

import aioimaplib
from src.config import Config
from fastmcp import (
    Context,
    FastMCP,
)
from html2text import html2text


def setup_tools(
    mcp: FastMCP,
    config: Config,
    _send_raw_email: callable,
    _fetch_emails: callable,
    _decode_mime_words: callable,
    _clean_email_body: callable,
):
    @mcp.tool(title="send_email")
    async def send_email(
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> dict:
        """Отправить электронное письмо одному или нескольким получателям."""
        cc = cc or []
        bcc = bcc or []

        return await _send_raw_email(to, cc, bcc, subject, body)

    @mcp.tool
    async def get_email(uid: str, ctx: Context) -> dict:
        """
        Получить письмо по UID и, при необходимости, предложить создать задачу.
        """
        client = aioimaplib.IMAP4_SSL(config.email.IMAP_HOST, config.email.IMAP_PORT)
        try:
            await client.wait_hello_from_server()
            await client.login(config.email.EMAIL_ADDRESS, config.email.EMAIL_PASSWORD)
            await client.select("INBOX")
            _, msg_data = await client.fetch(uid, "(RFC822)")
            raw = msg_data[1]
            parsed = email_lib.message_from_bytes(raw)

            # Извлечение тела
            body = ""
            if parsed.is_multipart():
                for part in parsed.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    # Пропускаем вложения
                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            try:
                                body = payload.decode(charset, errors="replace")
                            except LookupError:
                                body = payload.decode("utf-8", errors="replace")
                            break
                else:
                    # Если нет text/plain — попробуем text/html
                    for part in parsed.walk():
                        content_disposition = str(part.get("Content-Disposition", ""))
                        if "attachment" in content_disposition:
                            continue
                        if part.get_content_type() == "text/html":
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or "utf-8"
                                try:
                                    html = payload.decode(charset, errors="replace")
                                except LookupError:
                                    html = payload.decode("utf-8", errors="replace")
                                # Опционально: преобразовать HTML в текст
                                body = html  # или используйте html2text
                                break
            else:
                # Простое (не multipart) письмо
                payload = parsed.get_payload(decode=True)
                if payload:
                    charset = parsed.get_content_charset() or "utf-8"
                    try:
                        body = payload.decode(charset, errors="replace")
                    except LookupError:
                        body = payload.decode("utf-8", errors="replace")

            cleaned_body = _clean_email_body(html2text(body).strip())

            email_data = {
                "uid": uid,
                "from": _decode_mime_words(parsed.get("From", "")),
                "subject": _decode_mime_words(parsed.get("Subject", "")),
                "body": cleaned_body,
            }

            # === Генерация предложения задачи ===
            try:
                event_prompt = await ctx.prompt(
                    "calendar_should_create_enent_from_email",
                    {
                        "email_from": email_data["from"],
                        "email_subject": email_data["subject"],
                        "email_body": email_data["body"],
                    },
                )
                suggestion = await ctx.sample(event_prompt)
                if suggestion.text.strip() != "NO_EVENT":
                    await ctx.info(f"✅ Предложено событие: {suggestion.text}")
            except Exception as e:
                # Не ломаем основной вызов, если промпт недоступен
                await ctx.error(f"Не удалось сгенерировать задачу: {e}")

            return email_data

        finally:
            try:
                await client.logout()
            except:
                pass

    @mcp.tool
    async def list_emails(limit: int = 10) -> dict:
        """Получить список последних писем (до limit штук)."""
        emails = await _fetch_emails(["ALL"], limit)
        return {"emails": emails}

    @mcp.tool
    async def search_emails_by_sender(from_email: str, limit: int = 10) -> dict:
        """Найти письма по адресу отправителя (подстрока в From)."""
        emails = await _fetch_emails(["HEADER", "FROM", from_email], limit)
        return {"emails": emails}

    @mcp.tool
    async def search_emails_by_date(
        since: str = None, before: str = None, limit: int = 10
    ) -> dict:
        """Найти письма по дате. Формат даты: YYYY-MM-DD."""
        criteria = []
        if since:
            from datetime import datetime

            dt = datetime.strptime(since, "%Y-%m-%d")
            criteria.extend(["SINCE", dt.strftime("%d-%b-%Y")])
        if before:
            dt = datetime.strptime(before, "%Y-%m-%d")
            criteria.extend(["BEFORE", dt.strftime("%d-%b-%Y")])
        if not criteria:
            criteria = ["ALL"]
        emails = await _fetch_emails(criteria, limit)
        return {"emails": emails}

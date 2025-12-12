import re
import aiosmtplib
import aioimaplib
import email as email_lib

from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config import Config

config = Config.load()


def _clean_email_body(body: str) -> str:
    # 1. Удаляем ВСЁ, что похоже на изображения: ![](...) — даже битые
    body = re.sub(r"!\$$[^$$]*\$$\s*$$[^)]*\)", "", body, flags=re.DOTALL)
    body = re.sub(r"!\$$[^)]*\)", "", body, flags=re.DOTALL)  # fallback
    body = re.sub(r"!\$$\s*\$$", "", body)  # ![]()

    # 2. Удаляем Markdown-ссылки вида [текст](mailto:...) или <[текст](url)>
    body = re.sub(r"<$$$[^$$]*$$\([^)]*\)>", "", body, flags=re.DOTALL)
    body = re.sub(r"$$$[^$$]*$$\([^)]*mailto:[^)]*\)", "", body, flags=re.DOTALL)
    body = re.sub(r"$$$[^$$]*$$\([^)]*\)", "", body, flags=re.DOTALL)

    # 3. Удаляем email-подобные вставки: <parol.zd2@yandex.ru>
    body = re.sub(r"<[^>]*@[^>]*>", "", body)

    # 4. Удаляем строки с "Кому:", "Тема:", датами вида "04.12.2025, 15:15"
    body = re.sub(
        r"(?i)^\s*(Кому|Тема|From|To|Date|Sent):.*$", "", body, flags=re.MULTILINE
    )
    body = re.sub(r"\d{2}\.\d{2}\.\d{4},\s*\d{2}:\d{2}.*", "", body)

    # 5. Удаляем горизонтальные разделители
    body = re.sub(r"^\s*[\\-–=]{3,}\s*$", "", body, flags=re.MULTILINE)

    # 6. Удаляем обрывки URL, параметров и мусора вроде "dbaf-08dd12d39b36&f=0"
    body = re.sub(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", body
    )  # UUID
    body = re.sub(r"&[a-z0-9]+=[^&\s]*", "", body, flags=re.IGNORECASE)  # &f=0, &id=...
    body = re.sub(r"https?://[^\s)]*", "", body)  # остаточные URL

    # 7. Удаляем пустые строки и лишние пробелы
    lines = [line.strip() for line in body.splitlines() if line.strip()]

    # 8. Оставляем только **первый блок до первой цитаты или пересылки**
    # Ищем признаки начала истории: "написал:", ":", ">", "04.12.2025"
    clean_lines = []
    for line in lines:
        if re.search(
            r"(написал|:.*<.*@.*>|^\d{2}\.\d{2}\.\d{4}|>.*$)", line, re.IGNORECASE
        ):
            break
        clean_lines.append(line)

    # 9. Собираем и убираем двойные пробелы
    result = "\n".join(clean_lines)
    result = re.sub(r"\s{2,}", " ", result)
    result = re.sub(r"\s*\n\s*", "\n", result).strip()

    return result


def _decode_mime_words(s):
    if not s:
        return ""
    decoded_parts = decode_header(s)
    parts = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            enc = encoding or "utf-8"
            try:
                parts.append(part.decode(enc))
            except (UnicodeDecodeError, LookupError):
                parts.append(part.decode("utf-8", errors="replace"))
        else:
            parts.append(part)
    return "".join(parts)


async def _send_raw_email(to, cc, bcc, subject, body):
    all_recipients = to + cc + bcc
    msg = MIMEMultipart("alternative")
    msg["From"] = config.email.EMAIL_ADDRESS
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    await aiosmtplib.send(
        msg,
        recipients=all_recipients,
        hostname=config.email.SMTP_HOST,
        port=config.email.SMTP_PORT,
        use_tls=True,
        username=config.email.EMAIL_ADDRESS,
        password=config.email.EMAIL_PASSWORD,
    )
    return {"status": "sent", "to": to, "subject": subject}


async def _fetch_emails(criteria: list, limit: int = 10):
    client = aioimaplib.IMAP4_SSL(config.email.IMAP_HOST, config.email.IMAP_PORT)
    try:
        await client.wait_hello_from_server()
        await client.login(config.email.EMAIL_ADDRESS, config.email.EMAIL_PASSWORD)
        await client.select("INBOX")
        _, data = await client.search(*criteria)
        ids = data[0].split()[-limit:] if data[0] else []
        emails = []
        for uid in ids:
            uid_str = uid.decode("utf-8")
            _, msg_data = await client.fetch(uid_str, "(RFC822)")
            raw = msg_data[1]
            parsed = email_lib.message_from_bytes(raw)
            emails.append(
                {
                    "uid": uid_str,
                    "from": _decode_mime_words(parsed.get("From", "")),
                    "subject": _decode_mime_words(
                        parsed.get("Subject", "(no subject)")
                    ),
                    "date": parsed.get("Date", ""),
                }
            )
        return emails
    finally:
        await client.logout()

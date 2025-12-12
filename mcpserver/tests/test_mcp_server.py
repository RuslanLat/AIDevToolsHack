# tests/test_mcp_server.py
import pytest
from fastmcp import Client
from main import create_app


@pytest.fixture
async def mcp_client():
    """In-memory клиент без сети."""
    app = create_app()
    async with Client(app) as client:
        yield client


async def test_server_has_tools(mcp_client):
    tools = await mcp_client.list_tools()
    names = {t.name for t in tools}
    assert "email_send_email" in names
    assert "calendar_list_calendar_events" in names


async def test_server_has_prompts(mcp_client):
    prompts = await mcp_client.list_prompts()
    names = {t.name for t in prompts}
    assert "calendar_generate_event_from_email" in names
    assert "email_summarize_inbox" in names


async def test_resource_calendar_today(mcp_client):
    resource = await mcp_client.read_resource("events://calendar/today")
    assert len(resource) == 1
    assert str(resource[0].uri) == "events://calendar/today"

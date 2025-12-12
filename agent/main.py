from pathlib import Path
from agno.agent.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAILike
from agno.os import AgentOS
from agno.os.interfaces.a2a import A2A
from agno.tools.mcp import MCPTools  # MCP tools integration


from src.config import Config

BASE_DIR = Path(__file__).parent
instructions_path = BASE_DIR / "instructions.txt"
config = Config()

with open(instructions_path, "r", encoding="utf-8") as f:
    instructions_text = f.read()

# Setup the database
db = SqliteDb(db_file="tmp/agentos.db")

# MCP Server connection (replace with your MCP server URL)
mcp_tools = MCPTools(transport="streamable-http", url=config.mcp.MCP_SERVER_URL)


# Create A2A-capable agent with MCP tools
mcp_agent = Agent(
    name="MCP_Agent",
    model=OpenAILike(
        provider="GigaChat",
        id=config.llm.LLM_MODEL,
        name=config.llm.LLM_MODEL,
        base_url=config.llm.LLM_API_BASE,
        api_key=config.llm.LLM_API_KEY,
    ),
    instructions=instructions_text,
    tools=[mcp_tools],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)

# # Initialize A2A with the agent
a2a_interface = A2A(agents=[mcp_agent])


# # AgentOS with interfaces
agent_os = AgentOS(
    agents=[mcp_agent],
    interfaces=[a2a_interface],  # Pass A2A via interfaces
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="main:app", port=8080)

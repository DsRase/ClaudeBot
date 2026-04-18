from langchain_core.tools import tool

from src.agent.tools import fetch_url, read_full_history, search_web
from src.config import AgentMessages


@tool("search_web", description=AgentMessages.tool_descriptions_for_llm["search_web"])
async def search_web_tool(query: str, max_results: int | None = None) -> list[dict]:
    """LangChain-обёртка над search_web."""
    return await search_web(query, max_results=max_results)


@tool("fetch_url", description=AgentMessages.tool_descriptions_for_llm["fetch_url"])
async def fetch_url_tool(url: str) -> str:
    """LangChain-обёртка над fetch_url."""
    return await fetch_url(url)


ALL_TOOLS = [search_web_tool, fetch_url_tool]


def make_chat_scoped_tools(chat_id: int) -> list:
    """Билдит тулы, которым нужен chat_id (захвачен в замыкание)."""

    @tool("read_full_history", description=AgentMessages.tool_descriptions_for_llm["read_full_history"])
    async def read_full_history_tool() -> str:
        return await read_full_history(chat_id)

    return [read_full_history_tool]

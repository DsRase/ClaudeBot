from langchain_core.tools import tool

from src.agent.tools import fetch_url, read_full_history, search_web
from src.agent.tools.adaptive import choose_model
from src.agent.tools.memory import clear_user_memory_fn, get_user_memory_fn, set_user_memory_fn
from src.config import AgentMessages


@tool("search_web", description=AgentMessages.tool_descriptions_for_llm["search_web"])
async def search_web_tool(query: str, max_results: int | None = None) -> list[dict]:
    """LangChain-обёртка над search_web."""
    return await search_web(query, max_results=max_results)


@tool("fetch_url", description=AgentMessages.tool_descriptions_for_llm["fetch_url"])
async def fetch_url_tool(url: str) -> str:
    """LangChain-обёртка над fetch_url."""
    return await fetch_url(url)


@tool("choose_model", description=AgentMessages.tool_descriptions_for_llm_selector["choose_model"])
async def choose_model_tool(model: str) -> str:
    """LangChain-обёртка для structured-output выбора модели."""
    return await choose_model(model)


def make_chat_scoped_tools(chat_id: int) -> list:
    """Билдит тулы, которым нужен chat_id (захвачен в замыкание)."""

    @tool("read_full_history", description=AgentMessages.tool_descriptions_for_llm["read_full_history"])
    async def read_full_history_tool() -> str:
        return await read_full_history(chat_id)

    return [read_full_history_tool]


def make_user_memory_tools(user_id: int) -> list:
    """Билдит тулы памяти для конкретного юзера (user_id захвачен в замыкание)."""

    @tool("read_user_memory", description=AgentMessages.tool_descriptions_for_llm["read_user_memory"])
    async def read_user_memory_tool() -> str:
        return await get_user_memory_fn(user_id)

    @tool("write_user_memory", description=AgentMessages.tool_descriptions_for_llm["write_user_memory"])
    async def write_user_memory_tool(content: str) -> str:
        return await set_user_memory_fn(user_id, content)

    @tool("clear_user_memory", description=AgentMessages.tool_descriptions_for_llm["clear_user_memory"])
    async def clear_user_memory_tool() -> str:
        return await clear_user_memory_fn(user_id)

    return [read_user_memory_tool, write_user_memory_tool, clear_user_memory_tool]

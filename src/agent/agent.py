import json
import re
from typing import Awaitable, Callable

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.agent.langTools import ALL_TOOLS
from src.config import AgentMessages, get_settings
from src.storage.schemas import ChatMessage
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

PermissionRequester = Callable[[str, str], Awaitable[bool]]

_TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}


def _dump_msg(msg: ChatMessage) -> str:
    return json.dumps(msg.model_dump(mode="json"), ensure_ascii=False)


def _render_history(history: list[ChatMessage]) -> str:
    """Сворачивает историю в одну строку: блок контекста + блок триггерного сообщения (JSONL)."""
    if not history:
        return "=== Message to reply to NOW ===\n(no message)"
    *context, trigger = history
    lines = []
    if context:
        lines.append("=== Chat history (context only, do not respond to these) ===")
        lines.extend(_dump_msg(m) for m in context)
        lines.append("")
    lines.append("=== Message to reply to NOW ===")
    lines.append(_dump_msg(trigger))
    return "\n".join(lines)


def _extract_text(content) -> str:
    """Достаёт текст из ответа модели — поддерживает строку и список content-блоков Anthropic."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


async def _execute_tool_call(call: dict, permission_requester: PermissionRequester) -> ToolMessage:
    """Спрашивает разрешение, вызывает тулу и возвращает ToolMessage с результатом или причиной отказа."""
    tool_name = call["name"]
    tool_args = call.get("args", {})
    tool_id = call["id"]
    description = AgentMessages.tool_descriptions_for_user.get(tool_name, tool_name)

    allowed = await permission_requester(tool_name, description)
    if not allowed:
        logger.info(f"tool '{tool_name}' отклонён юзером (id={tool_id})")
        return ToolMessage(content="User denied permission to use this tool.", tool_call_id=tool_id)

    tool = _TOOLS_BY_NAME.get(tool_name)
    if tool is None:
        logger.warning(f"LLM попросила неизвестную тулу: {tool_name}")
        return ToolMessage(content=f"Unknown tool: {tool_name}", tool_call_id=tool_id)

    try:
        result = await tool.ainvoke(tool_args)
    except Exception as e:
        logger.warning(f"tool '{tool_name}' упал: {e!r}")
        return ToolMessage(content=f"Error while calling tool: {e}", tool_call_id=tool_id)

    return ToolMessage(content=str(result), tool_call_id=tool_id)


async def ask(
    history: list[ChatMessage],
    is_premium: bool = False,
    permission_requester: PermissionRequester | None = None,
) -> str:
    """Отправляет историю в LLM, крутит tool-calling loop, возвращает финальный текстовый ответ."""
    settings = get_settings()
    model = settings.premium_model if is_premium else settings.default_model
    logger.debug(f"Запрос к модели {model}, сообщений в контексте: {len(history)}")

    llm = ChatAnthropic(
        model=model,
        anthropic_api_key=settings.anthropic_api_key,
        timeout=120,
        max_tokens=settings.max_tokens,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS) if permission_requester is not None else llm

    messages = [
        SystemMessage(content=AgentMessages.system_prompt),
        HumanMessage(content=_render_history(history)),
    ]

    response = None
    for iteration in range(settings.agent_max_iterations):
        response = await llm_with_tools.ainvoke(messages)

        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls or permission_requester is None:
            if tool_calls and permission_requester is None:
                logger.warning("LLM запросила тулы, но permission_requester не задан — игнорируем")
            break

        messages.append(response)
        logger.info(f"итерация {iteration + 1}: модель попросила {len(tool_calls)} tool_call(s)")
        for call in tool_calls:
            tool_msg = await _execute_tool_call(call, permission_requester)
            messages.append(tool_msg)
    else:
        logger.warning(
            f"agent: достигнут cap итераций ({settings.agent_max_iterations}), "
            f"делаем финальный вызов без тул для текстового ответа"
        )
        response = await llm.ainvoke(messages)

    content = _extract_text(response.content if response else "")
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    logger.debug(f"Получен ответ от модели, длина: {len(content)}")
    return content

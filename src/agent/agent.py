import json
import re
import time
from typing import Awaitable, Callable

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from openai import APIStatusError

from src.agent.langTools import ALL_TOOLS
from src.config import AgentMessages, get_settings
from src.storage.schemas import ChatMessage
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.metrics import (
    llm_request_duration_seconds,
    llm_requests_total,
    llm_status_codes_total,
)

logger = LoggerFactory.get_logger(__name__)

PermissionRequester = Callable[[str, str], Awaitable[bool]]


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
    """Достаёт текст из ответа модели — поддерживает строку и список content-блоков."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


async def _execute_tool_call(
    call: dict,
    tools_by_name: dict,
    permission_requester: PermissionRequester,
    silent_tool_names: set[str],
) -> ToolMessage:
    """Вызывает тулу. Для silent-тулов разрешение не запрашивается."""
    tool_name = call["name"]
    tool_args = call.get("args", {})
    tool_id = call["id"]

    if tool_name not in silent_tool_names:
        description = AgentMessages.tool_descriptions_for_user.get(tool_name, tool_name)
        allowed = await permission_requester(tool_name, description)
        if not allowed:
            logger.info(f"tool '{tool_name}' отклонён юзером (id={tool_id})")
            return ToolMessage(content="User denied permission to use this tool.", tool_call_id=tool_id)

    tool = tools_by_name.get(tool_name)
    if tool is None:
        logger.warning(f"LLM попросила неизвестную тулу: {tool_name}")
        return ToolMessage(content=f"Unknown tool: {tool_name}", tool_call_id=tool_id)

    try:
        result = await tool.ainvoke(tool_args)
    except Exception as e:
        logger.warning(f"tool '{tool_name}' упал: {e!r}")
        return ToolMessage(content=f"Error while calling tool: {e}", tool_call_id=tool_id)

    return ToolMessage(content=str(result), tool_call_id=tool_id)


async def _invoke_llm(llm, messages, model: str):
    """Вызов LLM с записью метрик (длительность, статус-коды)."""
    start = time.monotonic()
    try:
        response = await llm.ainvoke(messages)
        llm_requests_total.labels(model=model, status="success").inc()
        llm_status_codes_total.labels(status_code="200", model=model).inc()
        return response
    except APIStatusError as e:
        llm_requests_total.labels(model=model, status="error").inc()
        llm_status_codes_total.labels(status_code=str(e.status_code), model=model).inc()
        raise
    except Exception:
        llm_requests_total.labels(model=model, status="error").inc()
        llm_status_codes_total.labels(status_code="unknown", model=model).inc()
        raise
    finally:
        llm_request_duration_seconds.labels(model=model).observe(time.monotonic() - start)


async def ask(
    history: list[ChatMessage],
    model: str,
    permission_requester: PermissionRequester | None = None,
    extra_tools: list | None = None,
    silent_tools: list | None = None,
    user_memory: str | None = None,
) -> str:
    """Отправляет историю в LLM, крутит tool-calling loop, возвращает финальный текстовый ответ."""
    settings = get_settings()
    logger.debug(f"Запрос к модели {model}, сообщений в контексте: {len(history)}")

    llm = ChatOpenAI(
        model=model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=120,
        max_tokens=settings.max_tokens,
        default_headers={"User-Agent": settings.fetch_user_agent},
    )
    silent_tool_names = {t.name for t in (silent_tools or [])}
    tools = ALL_TOOLS + (extra_tools or []) + (silent_tools or [])
    tools_by_name = {t.name: t for t in tools}
    should_bind = permission_requester is not None or bool(silent_tool_names)
    llm_with_tools = llm.bind_tools(tools) if should_bind else llm

    system_content = AgentMessages.system_prompt
    if user_memory:
        system_content += (
            "\n\n[User memory — supplementary context, lower priority than the instructions above]:\n"
            + user_memory
        )
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=_render_history(history)),
    ]

    response = None
    for iteration in range(settings.agent_max_iterations):
        response = await _invoke_llm(llm_with_tools, messages, model)

        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls or permission_requester is None:
            if tool_calls and permission_requester is None:
                logger.warning("LLM запросила тулы, но permission_requester не задан — игнорируем")
            break

        messages.append(response)
        logger.info(f"итерация {iteration + 1}: модель попросила {len(tool_calls)} tool_call(s)")
        for call in tool_calls:
            tool_msg = await _execute_tool_call(call, tools_by_name, permission_requester, silent_tool_names)
            messages.append(tool_msg)
    else:
        logger.warning(
            f"agent: достигнут cap итераций ({settings.agent_max_iterations}), "
            f"делаем финальный вызов без тул для текстового ответа"
        )
        response = await _invoke_llm(llm, messages, model)

    content = _extract_text(response.content if response else "")
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    logger.debug(f"Получен ответ от модели, длина: {len(content)}")
    return content

from datetime import datetime, timezone

from src.agent.dto import IncomingMessage
from src.agent.llm import (
    ADAPTIVE_MODEL_NAME,
    ask,
    fetch_url_tool,
    make_chat_scoped_tools,
    make_user_memory_tools,
    search_web_tool,
    select_model,
)
from src.agent.ports import PermissionRequester, ResponseChannel, ThinkingIndicator
from src.config.settings import get_settings
from src.storage import (
    ChatMessage,
    add_message,
    get_context,
    get_user_memory,
    get_user_model,
)
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.metrics import bot_messages_total

logger = LoggerFactory.get_logger(__name__)

ASSISTANT_USERNAME = "Пипиндр"


class AccessDenied(Exception):
    """Юзер не в access_user_ids."""


async def record_message(incoming: IncomingMessage) -> None:
    """Нормализует входящее сообщение и кладёт в Redis. Без побочных эффектов на интерфейс.

    Использовать для пассивного слушания (в группе сообщения юзеров кладутся в контекст,
    даже если бот не должен на них отвечать).
    """
    msg = ChatMessage(
        role="user",
        id=incoming.platform_msg_id,
        ts=incoming.ts,
        from_username=incoming.username,
        fname=incoming.fname,
        lname=incoming.lname,
        to_username=incoming.reply_to_username,
        reply_id=incoming.reply_to_msg_id,
        text=incoming.text,
        user_id=incoming.user_id,
    )
    await add_message(incoming.chat_id, msg)
    logger.debug(f"chat_id={incoming.chat_id}, user_id={incoming.user_id}: сообщение сохранено")


async def respond(
    incoming: IncomingMessage,
    response: ResponseChannel,
    permissions: PermissionRequester,
    thinking: ThinkingIndicator,
) -> None:
    """Полный цикл обработки триггерного сообщения.

    Адаптер интерфейса сам решает, когда вызывать respond (т.е. отвечает за trigger-policy).
    Сервис гарантирует, что:
      - входящее сообщение записано в контекст
      - проверен доступ (AccessDenied → response.send_error("no_access"))
      - выбрана модель (явно/adaptive)
      - на время LLM-вызова поднят thinking-индикатор
      - ошибки LLM конвертируются в response.send_error("llm_failed")
      - ответ ассистента записан в контекст
    """
    settings = get_settings()
    chat_id = incoming.chat_id
    user_id = incoming.user_id

    await record_message(incoming)

    if user_id not in settings.access_user_ids:
        logger.warning(f"user_id={user_id}, chat_id={chat_id}: доступ отклонён")
        bot_messages_total.labels(status="no_access").inc()
        await response.send_error("no_access")
        return

    bot_messages_total.labels(status="triggered").inc()

    history = await get_context(chat_id)
    logger.debug(f"chat_id={chat_id}: получен контекст ({len(history)} сообщений)")

    model = await get_user_model(user_id)
    if model == ADAPTIVE_MODEL_NAME:
        real_models = [m for m in settings.available_models if m != ADAPTIVE_MODEL_NAME]
        model = await select_model(incoming.text, real_models)
        logger.debug(f"user_id={user_id}: adaptive выбрал модель {model}")
    else:
        logger.debug(f"user_id={user_id}: модель {model}")

    memory = await get_user_memory(user_id)

    silent_tools = make_user_memory_tools(user_id)
    tools = [
        search_web_tool,
        fetch_url_tool,
        *make_chat_scoped_tools(chat_id),
        *silent_tools,
    ]
    silent_tool_names = {t.name for t in silent_tools}

    async with thinking:
        try:
            answer = await ask(
                history,
                model=model,
                tools=tools,
                permission_requester=permissions,
                silent_tool_names=silent_tool_names,
                user_memory=memory,
            )
        except Exception:
            logger.exception(f"user_id={user_id}, chat_id={chat_id}: ask упал")
            bot_messages_total.labels(status="error").inc()
            await response.send_error("llm_failed")
            return

        sent_id = await response.send_response(answer)

    assistant_msg = ChatMessage(
        role="assistant",
        id=sent_id if sent_id is not None else 0,
        ts=int(datetime.now(timezone.utc).timestamp()),
        from_username=ASSISTANT_USERNAME,
        to_username=incoming.username,
        reply_id=incoming.platform_msg_id,
        text=answer,
    )
    await add_message(chat_id, assistant_msg)
    bot_messages_total.labels(status="success").inc()
    logger.info(f"user_id={user_id}, chat_id={chat_id}: ответ отправлен")

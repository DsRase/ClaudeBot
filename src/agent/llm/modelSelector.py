from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agent.llm.langTools import choose_model_tool
from src.config import AgentMessages
from src.config.settings import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

ADAPTIVE_MODEL_NAME = "adaptive"

logger = LoggerFactory.get_logger(__name__)


async def select_model(trigger_text: str, available_models: list[str]) -> str:
    """Выбирает оптимальную модель для запроса через selector-модель."""
    settings = get_settings()

    llm = ChatOpenAI(
        model=settings.adaptive_selector_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=30,
        max_tokens=64,
        default_headers={"User-Agent": settings.fetch_user_agent},
    ).bind_tools([choose_model_tool], tool_choice="choose_model")

    models_desc = "\n".join(f"- {m}" for m in available_models)
    system = AgentMessages.selector_system_prompt + f"\n\nAvailable models:\n{models_desc}"

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=trigger_text),
        ])
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            chosen = tool_calls[0].get("args", {}).get("model", "")
            if chosen in available_models:
                logger.info(f"adaptive: выбрана модель '{chosen}' для: {trigger_text[:80]!r}")
                return chosen
    except Exception as e:
        logger.warning(f"adaptive: ошибка выбора модели: {e!r}")

    fallback = settings.default_model
    logger.warning(f"adaptive: fallback на '{fallback}'")
    return fallback

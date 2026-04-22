from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.agent.permissions import get_permission_state
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

router = Router()


_ACTIONS = {
    "allow": ("✅ Разрешено", True, False),
    "allow_session": ("🔁 Разрешено до конца сессии", True, True),
    "deny": ("❌ Запрещено", False, False),
}


@router.callback_query(F.data.startswith("perm:"))
async def on_permission_click(callback: CallbackQuery):
    """Обрабатывает клик по кнопке permission-запроса. Только инициатор может решить."""
    _, request_id, action = callback.data.split(":", 2)

    state = get_permission_state()
    request = state.get_request(request_id)
    if request is None:
        await callback.answer("Запрос уже неактуален.")
        return

    if callback.from_user.id != request.initiator_user_id:
        who = f"@{request.initiator_username}" if request.initiator_username else "инициатор"
        await callback.answer(f"Только {who} может решить.", show_alert=True)
        return

    if action not in _ACTIONS:
        await callback.answer("Неизвестное действие.")
        return
    label, result, save_for_session = _ACTIONS[action]

    request.result = result
    request.save_for_session = save_for_session
    request.event.set()

    logger.info(
        f"user_id={callback.from_user.id}: клик по '{request.tool_name}' "
        f"(request_id={request_id}, action={action})"
    )

    msg = callback.message
    original_html = msg.html_text or msg.text or ""
    await msg.edit_text(
        f"<s>{original_html}</s>\n\n{label}",
        parse_mode="HTML",
        reply_markup=None,
    )
    await callback.answer()

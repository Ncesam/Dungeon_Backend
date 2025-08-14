import contextvars

from logics.botmanager import BotManager

bot_manager_ctx: contextvars.ContextVar[BotManager | None] = contextvars.ContextVar("bot_manager_ctx", default=None)

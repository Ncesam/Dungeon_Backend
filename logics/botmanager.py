import multiprocessing
from collections import defaultdict
from typing import Dict, List

from pydantic.v1.schema import schema
from sqlalchemy.ext.asyncio import AsyncSession

from logics.lots_bot import VKBot
from logics.vk_deleter import run_vk_deleter_process
from shared.logger import logger
from shared.schemas import StartBotSchema

log = logger.get_logger()


class BotManager:
    def __init__(self, session: AsyncSession) -> None:
        self.active_monitors: Dict[int, multiprocessing.Process] = {}
        self.deleter_monitors: Dict[str, multiprocessing.Process] = {}
        self.user_map: Dict[int, List[StartBotSchema]] = defaultdict(list)
        self.vk_bot = VKBot(session=session)

    async def start_monitoring(self, schema: StartBotSchema):
        self.user_map[schema.item_id].append(schema)

        if schema.item_id not in self.active_monitors:
            log.info(f"Запускаем мониторинг лота {schema.item_id}")
            process = multiprocessing.Process(target=self.vk_bot.monitoring, args=(
                schema.item_id, schema.max_price, schema.user_id, schema.auth_key, schema.delay, schema.name))
            self.active_monitors[schema.item_id] = process
            self.start_vk_deleter(schema.vk_token, "Подземелья колодца")
        else:
            log.info(f"Мониторинг для {schema.item_id} уже запущен. Добавлен пользователь {schema.user_id}")

    def remove_user(self, item_id: int, user_id: int):
        self.user_map[item_id] = [u for u in self.user_map[item_id] if u[0] != user_id]
        log.info(f"👋 Пользователь {user_id} удалён из лота {item_id}")
        if not self.user_map[item_id]:
            log.info(f"🛑 Остановка мониторинга лота {item_id} (нет пользователей)")
            task: multiprocessing.Process = self.active_monitors.pop(item_id, None)
            if task.is_alive():
                task.kill()
            del self.user_map[item_id]

    def start_vk_deleter(self, token: str, group_name: str):
        if token not in self.deleter_monitors:
            p = multiprocessing.Process(
                target=run_vk_deleter_process,
                args=(token, group_name),
                daemon=True
            )
            p.start()
            self.deleter_monitors[token] = p
            log.info(f"Процесс VkDeleter для {token} запущен (PID {p.pid})")
        else:
            log.info(f"Процесс для {token} уже запущен")

    def stop_vk_deleter(self, token: str):
        proc = self.deleter_monitors.pop(token, None)
        if proc and proc.is_alive():
            proc.terminate()
            log.info(f"Процесс для {token} остановлен")

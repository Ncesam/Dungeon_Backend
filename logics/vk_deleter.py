import asyncio
from typing import Optional

from logics.vk_api import VkApiAsync
from shared.logger import logger

log = logger.get_logger()


class VkDeleter:
    DELETE_PATTERNS = [
        "Для покупки любого из лотов",
        "Вы успешно приобрели с аукциона предмет"
    ]

    def __init__(self, token: str, target_group_name: str):
        self.token = token
        self.target_group_name = target_group_name
        self.api: Optional[VkApiAsync] = None
        self.group_peer_id: Optional[int] = None

    async def find_group_peer_id(self):
        conversations = await self.api.get_conversations()
        items = conversations.get("items", [])
        for conv in items:
            peer = conv["conversation"]["peer"]
            if peer["type"] == "group":
                group_info = await self.api.get_group_by_id(abs(peer["id"]))
                if group_info["groups"][0] and group_info["groups"][0]["name"] == self.target_group_name:
                    log.info(f"Нашёл группу: {self.target_group_name}")
                    return peer["id"]
        log.warning("Группа не найдена")
        return None

    async def process_messages(self):
        history = await self.api.get_history(peer_id=self.group_peer_id)
        items = history.get("items", [])
        for msg in items:
            if any(pattern in msg.get("text", "") for pattern in self.DELETE_PATTERNS):
                await self.api.delete_message(message_id=msg["id"], peer_id=self.group_peer_id)
                log.info(f"Удалено сообщение ID={msg['id']}")

    async def run(self):
        async with VkApiAsync(self.token) as api:
            self.api = api
            self.group_peer_id = await self.find_group_peer_id()
            if not self.group_peer_id:
                return
            while True:
                await self.process_messages()
                await asyncio.sleep(30)


def run_vk_deleter_process(token: str, group_name: str):
    deleter = VkDeleter(token, group_name)
    asyncio.run(deleter.run())

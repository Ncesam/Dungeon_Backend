from typing import Optional, List

import aiohttp

from shared.logger import logger

log = logger.get_logger()


class VkApiAsync:
    API_URL = "https://api.vk.com/method/"
    API_VERSION = "5.199"

    def __init__(self, token: str):
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def call(self, method: str, **params) -> dict:
        params.update({
            "access_token": self.token,
            "v": self.API_VERSION
        })
        async with self.session.get(f"{self.API_URL}{method}", params=params) as resp:
            data = await resp.json()
            if "error" in data:
                log.error(f"VK API Error: {data['error']}")
                return {}
            return data.get("response", {})

    async def get_conversations(self, count: int = 15) -> dict:
        return await self.call("messages.getConversations", count=count)

    async def get_group_by_id(self, group_id: int) -> List[dict]:
        return await self.call("groups.getById", group_id=group_id)

    async def get_history(self, peer_id: int, count: int = 150, offset: int = 0) -> dict:
        return await self.call("messages.getHistory", peer_id=peer_id, count=count, offset=offset)

    async def delete_message(self, message_id: int, peer_id: int):
        return await self.call("messages.delete", message_id=message_id, peer_id=peer_id)

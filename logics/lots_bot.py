import asyncio
import json
import re
import traceback
from typing import List

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import get_session
from database.services import LotService
from shared.logger import logger
from shared.schemas import LotSchema

log = logger.get_logger()


class VKBot:
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36',
    }

    def __init__(self, session: AsyncSession):
        self.lot_service = LotService(session)

    async def buy_lot(self, lot_id: int, user_id: int, auth_key: str):
        url = "https://vip3.activeusers.ru/app.php"
        params = {
            'act': 'a_program_say',
            'viewer_id': str(user_id),
            'auth_key': auth_key
        }
        data = {
            'ch': f'u{user_id}',
            'text': f'Купить лот {lot_id}',
            'context': '1',
            'messages[0][message]': f'Купить лот {lot_id}',
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, data=data, headers=self.headers) as resp:
                    resp.raise_for_status()
                    log.info(f"✅ Лот {lot_id} куплен для пользователя {user_id}")
        except aiohttp.ClientError as e:
            log.error(f"❌ Ошибка при покупке лота {lot_id} пользователю {user_id}: {e}")
            log.debug(traceback.format_exc())

    async def get_cheapest_lots(self, item_id: int, auth_key: str, max_price: int, user_id: int) -> int | list[
        LotSchema] | None:
        url = "https://vip3.activeusers.ru/app.php"
        params = {
            'act': 'a_program_run',
            'viewer_id': str(user_id),
            'auth_key': auth_key
        }
        data = f"code=51132l145l691d2fbd8b124d57&context=1&vars[item][id]={item_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, data=data, headers=self.headers) as resp:
                    resp.raise_for_status()

                    response_text = await resp.text()
                    log.debug(f"📨 Ответ от аукциона:\n{response_text}")
                    response_json = json.loads(response_text)

                    lots_text = response_json['message'][0]['message']
                    list_lots = lots_text.split('\n')

                    if list_lots[0].startswith("🚫Вы просматриваете аукцион слишком часто"):
                        return 1

                    cheapest_lots = []
                    for lot in list_lots:
                        try:
                            if not lot.strip() or lot.startswith('\r'):
                                break
                            match = re.search(r'\((\d+)\)', lot)
                            if match:
                                lot_id = int(match.group(1))
                                lot = re.sub(r'\(\d+\)', '', lot).strip()
                            else:
                                log.info("Лот ID не найден")
                                continue
                            parts = lot.split(" ")
                            count = int(parts[0].split('*')[0])
                            price = int(parts[2])
                            name_array = parts[3:-1]
                            name = " ".join(name_array)
                            if (price / count) <= max_price:
                                cheapest_lots.append(LotSchema(id=lot_id, name=name, price=price))
                        except Exception as ex:
                            log.warning(f"⚠️ Ошибка при обработке лота: '{lot}': {ex}")
                            continue
                    return cheapest_lots
        except aiohttp.ClientError as e:
            log.error(f"❌ Ошибка при получении лотов: {e}")
            log.debug(traceback.format_exc())
            return

    async def monitoring(self, item_id: int, max_price: int, user_id: int, auth_key: str, delay: int, name: str):
        log.info(f"🚀 Запущен мониторинг для item_id={item_id}, интервал: {delay} мин., максимальная цена: {max_price}")

        while True:
            try:
                cheapest_lots = await self.get_cheapest_lots(item_id, auth_key, max_price, user_id)
                if cheapest_lots is None:
                    continue
                if isinstance(cheapest_lots, int):
                    log.info(f"⏳ {item_id} стоит на ожидании (частый просмотр). Пауза на 1 час.")
                    await asyncio.sleep(3600)
                    continue
                if isinstance(cheapest_lots, list) and len(cheapest_lots) == 0:
                    log.info(f"⏳ {item_id}: нет подходящих лотов стоит на паузу на {delay} минут")
                    await asyncio.sleep(delay * 60)
                    continue
                for lot in cheapest_lots:
                    await self.buy_lot(lot.id, user_id, auth_key)
                    await self.lot_service.add_lot(LotSchema(id=lot.id, name=lot.name, price=lot.price))
                    log.info(f"✅ Куплен лот {lot.id} для пользователя {user_id}. Товар: {lot.name}, цена: {lot.price}.")
                    await asyncio.sleep(10)

                await asyncio.sleep(delay * 60)
            except Exception as e:
                log.error(f"❌ Ошибка в процессе мониторинга item_id={item_id}: {e}")
                log.debug(traceback.format_exc())
                await asyncio.sleep(60)

    async def view_lots(self) -> List[LotSchema] | None:
        try:
            lots = await self.lot_service.get_lots()
            return lots
        except Exception as e:
            log.error(f"❌ Ошибка при отправке лотов: {e}")
            log.debug(traceback.format_exc())


def start_monitoring(item_id: int, max_price: int, user_id: int, auth_key: str, delay: int, name: str):
    async def async_impl():
        async with get_session() as session:
            vk_bot = VKBot(session)
            log.info(f"Мониторинг лота {item_id} статус: Запуск")
            await vk_bot.monitoring(item_id, max_price, user_id, auth_key, delay, name)

    asyncio.run(async_impl())

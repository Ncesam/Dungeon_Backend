import vk_api

from logger import logger


class VkDeleter:
    def __init__(self, token: str = None):
        self.vk_session = vk_api.VkApi(
            token=token)
        self.vk = self.vk_session.get_api()
        self.id_group = self.get_group()
        self.run()

    def run(self):
        while True:
            self.loop()

    def loop(self):
        history_messages = self.vk.messages.getHistory(count=150, offset=0,
                                                       peer_id=self.id_group)
        for history_message in history_messages['items']:
            if "Для покупки любого из лотов" in history_message['text']:
                self.delete_message(message_id=history_message['id'], peer_id=self.id_group)
            elif "Вы успешно приобрели с аукциона предмет" in history_message['text']:
                self.delete_message(message_id=history_message['id'], peer_id=self.id_group)

    def get_group(self):
        list_conversation = self.vk.messages.getConversations(count=15)
        logger.info("Получены все чаты")
        for conversation in list_conversation['items']:
            if conversation['conversation']['peer']['type'] == 'group':
                group = self.vk.groups.getById(group_id=abs(conversation['conversation']['peer']['id']))
                if group[0]['name'] == "Подземелье колодца":
                    logger.info("Нашел группу")
                    return conversation['conversation']['peer']['id']

    def delete_message(self, message_id, peer_id):
        self.vk.messages.delete(message_id=message_id, peer_id=peer_id)
        logger.debug('Message deleted')

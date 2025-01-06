import copy
import logging
import multiprocessing
import socket
import time

import psutil
import requests

import database
import config


class Server:
    def __init__(self):
        self.bot = VKBot()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            datefmt='%d/%m/%Y %I:%M:%S %p', handlers=[logging.StreamHandler(), logging.FileHandler('Log.log')], filemode='a')
        logging.info("Сервер инициализирован.")

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((config.env['SERVER_IP'], int(config.env['SERVER_PORT'])))
        sock.listen(2)
        logging.info("Сервер запущен и ожидает подключения.")
        while True:
            conn, addr = sock.accept()
            logging.info("Подключение от %s.", addr)
            try:
                data = conn.recv(4096).decode()
                logging.info("Получены данные: %s", data)
                if "start monitoring" in data:
                    self.start_monitoring(data)
                if "stop monitoring" in data:
                    self.stop_monitoring(data)
            except Exception as e:
                logging.error("Ошибка при обработке подключения: %s", e)

    def find_process(self, name):
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            try:
                if proc.info['name'] == name:
                    logging.info("Процесс найден: %s", name)
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logging.warning("Ошибка при проверке процесса %s: %s", name, e)
        logging.info("Процесс %s не найден.", name)
        return None

    def start_monitoring(self, data):
        args = self.parse_args(data)
        if self.find_process(str(args["item_id"])):
            logging.warning("Мониторинг уже запущен для item_id=%s.", args["item_id"])
            return
        monitoring_process = multiprocessing.Process(
            target=self.bot.monitoring,
            name=str(args["item_id"]),
            args=(args["item_id"], args["max_price"], args["user_id"], args["delay"])
        )
        monitoring_process.start()
        logging.info("Мониторинг запущен для item_id=%s.", args["item_id"])
        return monitoring_process.name

    def stop_monitoring(self, data):
        args = self.parse_args(data)
        process = self.find_process(str(args["item_id"]))
        if process:
            process.terminate()
            process.join()
            logging.info("Мониторинг остановлен для item_id=%s.", args["item_id"])
            return 1
        else:
            logging.warning("Процесс для item_id=%s не найден.", args["item_id"])
            return 0

    def parse_args(self, data):
        data = data.split(' ')
        parsed_data = {}
        for item in data:
            if item.startswith("item_id="):
                parsed_data[item.split("=")[0]] = item.split("=")[1]
            if item.startswith("max_price="):
                parsed_data[item.split("=")[0]] = item.split("=")[1]
            if item.startswith("user_id="):
                parsed_data[item.split("=")[0]] = item.split("=")[1]
            if item.startswith("delay="):
                parsed_data[item.split("=")[0]] = item.split("=")[1]
            if item.startswith("name="):
                parsed_data[item.split("=")[0]] = item.split("=")[1]
        logging.debug("Разобранные аргументы: %s", parsed_data)
        return parsed_data


class VKBot:
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36',
    }
    params = {
        'auth_key': '3a548454f70391405932bf4769761acc',
        'viewer_id': '214163323'
    }

    database_service = database.ServiceDatabase()

    def buy_lot(self, lot_id: int, user_id: int):
        param = copy.deepcopy(self.params)
        param['act'] = 'a_program_say'
        data = {
            'ch': f'u{user_id}',
            'text': f'Купить лот {lot_id}',
            'context': '1',
            'messages[0][message]': f'Купить лот {lot_id}',
        }
        try:
            requests.post(url="https://vip3.activeusers.ru/app.php", params=param, data=data,
                          headers=self.headers)
            logging.info("Лот %s куплен для пользователя %s.", lot_id, user_id)
        except Exception as e:
            logging.error("Ошибка при покупке лота %s: %s", lot_id, e)

    def monitoring(self, item_id: int, max_price: int, user_id: int, delay: int, name: str):
        logging.info("Запущен мониторинг для item_id=%s с интервалом %s секунд.", item_id, delay)
        while True:
            time.sleep(delay)
            try:
                cheapest_lots = self.get_cheapest_lots(item_id, max_price)
                for lot_id, price in cheapest_lots:
                    self.buy_lot(lot_id, user_id)
                    self.database_service.add_lot(lot_id, name, price)
            except Exception as e:
                logging.error("Ошибка в процессе мониторинга item_id=%s: %s", item_id, e)

    def get_cheapest_lots(self, item_id: int, max_price: int):
        param = copy.deepcopy(self.params)
        param['act'] = 'a_program_run'
        data = f"code=51132l145l691d2fbd8b124d57&context=1&vars[item][id]={item_id}"
        try:
            response = requests.post(url="https://vip3.activeusers.ru/app.php", params=param, data=data,
                                     headers=self.headers)
            messages = response.json()
            list_lots = messages['message'][0]['message']
            list_lots = list_lots.split("\n")
            cheapest_lots = []
            for lot in list_lots:
                try:
                    count = int(lot.split(" ")[0].split('*')[0])
                    price = int(lot.split(" ")[2])
                    lot_id = int(lot.split(" ")[4].strip().replace("(", '').replace(")", ''))
                    price_for_one = price / count
                    logging.debug("Обнаружен лот: %s", lot)
                    if price_for_one <= max_price:
                        cheapest_lots.append((lot_id, price))
                except Exception as ex:
                    logging.warning("Ошибка при обработке лота: %s", ex)
                    continue
            return cheapest_lots
        except Exception as e:
            logging.error("Ошибка при получении лотов: %s", e)
            return []


if __name__ == '__main__':
    server = Server()
    server.run()

import copy
import multiprocessing
import socket
import time
import psutil
import requests
import database
import config
from logger import logger


class Server:
    def __init__(self):
        self.bot = VKBot()
        logger.info("Сервер инициализирован.")
        self.active_processes = {}  # Для отслеживания активных процессов мониторинга

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((config.env['SERVER_IP'], int(config.env['SERVER_PORT'])))
        sock.listen(2)
        logger.info(f"Сервер запущен и ожидает подключения на {config.env['SERVER_IP']}:{config.env['SERVER_PORT']}.")
        while True:
            conn, addr = sock.accept()
            logger.info(f"Подключение от {addr}.")
            try:
                while True:
                    data = conn.recv(4096).decode()
                    if data:
                        logger.info(f"Получены данные: {data}")
                        if "start monitoring" in data:
                            self.start_monitoring(data, conn)
                        elif "stop monitoring" in data:
                            self.stop_monitoring(data, conn)
                    if not data:  # Если данные не получены, клиент мог отключиться
                        logger.warning(f"Соединение с {addr} разорвано.")
                        break  # Прерываем обработку для данного клиента
            except Exception as e:
                logger.error(f"Ошибка при обработке подключения: {e}")
            finally:
                conn.close()

    def find_process(self, name):
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            try:
                if proc.info['name'] == name:
                    logger.info(f"Процесс найден: {name}")
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"Ошибка при проверке процесса {name}: {e}")
        logger.info(f"Процесс {name} не найден.")
        return None

    def start_monitoring(self, data, conn):
        args = self.parse_args(data)
        if self.find_process(str(args["item_id"])):
            logger.warning(f"Мониторинг уже запущен для item_id={args['item_id']}.")
            return

        # Создаем процесс мониторинга и запускаем его
        args = (int(args["item_id"]), int(args["max_price"]), int(args["user_id"]), int(args["delay"]), args["name"], conn)
        monitoring_process = multiprocessing.Process(
            target=self.bot.monitoring,
            name=str(args[0]),
            args=args)
        monitoring_process.start()
        self.active_processes[args[0]] = monitoring_process  # Добавляем процесс в словарь активных процессов
        logger.info(f"Мониторинг запущен для item_id={args[0]}.")
        conn.send(f"Мониторинг запущен для item_id={args[0]}.".encode('utf-8'))

    def stop_monitoring(self, data, conn):
        args = self.parse_args(data)
        item_id = int(args["item_id"])
        process = self.active_processes.get(item_id)

        if process:
            process.terminate()  # Останавливаем процесс мониторинга
            process.join()  # Ожидаем завершения процесса
            del self.active_processes[item_id]  # Удаляем из активных процессов
            logger.info(f"Мониторинг остановлен для item_id={item_id}.")
            conn.send(f"Мониторинг остановлен для item_id={item_id}.".encode('utf-8'))
        else:
            logger.warning(f"Процесс для item_id={item_id} не найден.")
            conn.send(f"Процесс для item_id={item_id} не найден.".encode('utf-8'))

    def parse_args(self, data):
        # Преобразуем строку запроса в словарь
        parsed_data = {item.split('=')[0]: item.split('=')[1] for item in data.split(' ') if '=' in item}
        logger.debug(f"Разобранные аргументы: {parsed_data}")
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
            response = requests.post(url="https://vip3.activeusers.ru/app.php", params=param, data=data,
                                     headers=self.headers)
            response.raise_for_status()
            logger.info(f"Лот {lot_id} куплен для пользователя {user_id}.")
        except requests.RequestException as e:
            logger.error(f"Ошибка при покупке лота {lot_id}: {e}")

    def monitoring(self, item_id: int, max_price: int, user_id: int, delay: int, name: str, conn):
        logger.info(f"Запущен мониторинг для item_id={item_id} с интервалом {delay} секунд.")
        while True:
            try:
                cheapest_lots = self.get_cheapest_lots(item_id, max_price)
                if cheapest_lots == "Later":
                    logger.info(f"{item_id} стоит на ожидании в течении часа")
                    conn.send(f"{item_id} стоит на ожидании в течении часа".encode("utf-8"))
                    time.sleep(3600)  # Ждем 1 час
                    continue
                for lot_id, price in cheapest_lots:
                    self.buy_lot(lot_id, user_id)
                    self.database_service.add_lot(lot_id, name, price)
                    conn.send(f"Купил лот {lot_id} пользователю {user_id}. Имя товара {name} цена {price}.".encode('utf-8'))
                    time.sleep(5)
                time.sleep(delay * 60)
            except Exception as e:
                logger.error(f"Ошибка в процессе мониторинга item_id={item_id}: {e}")

    def get_cheapest_lots(self, item_id: int, max_price: int):
        param = copy.deepcopy(self.params)
        param['act'] = 'a_program_run'
        data = f"code=51132l145l691d2fbd8b124d57&context=1&vars[item][id]={item_id}"
        try:
            response = requests.post(url="https://vip3.activeusers.ru/app.php", params=param, data=data,
                                     headers=self.headers)
            response.raise_for_status()
            messages = response.json()
            list_lots = messages['message'][0]['message'].split("\n")
            cheapest_lots = []
            if list_lots[0] == "🚫Вы просматриваете аукцион слишком часто. Повторите попытку через час.":
                return "Later"
            for lot in list_lots:
                try:
                    if lot[0] == '\r':
                        break
                    count = int(lot.split(" ")[0].split('*')[0])
                    price = int(lot.split(" ")[2])
                    lot_id = int(lot.split(" ")[4].strip().replace("(", '').replace(")", ''))
                    price_for_one = price / count
                    if price_for_one <= max_price:
                        cheapest_lots.append((lot_id, price))
                except ValueError as ex:
                    logger.warning(f"Ошибка при обработке лота: {ex}")
                    continue
            return cheapest_lots
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении лотов: {e}")
            return []


if __name__ == '__main__':
    server = Server()
    server.run()

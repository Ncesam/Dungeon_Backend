import copy
import multiprocessing
import socket
import threading
import time
import psutil
import requests
import database
import config
from logger import logger
from vk import VkDeleter

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
                            self.start_deleter(data, conn)
                        elif "stop monitoring" in data:
                            self.stop_monitoring(data, conn)
                            self.stop_deleter(data, conn)
                        elif "view lots" in data:
                            self.view_lots(conn)
                    if not data:  # Если данные не получены, клиент мог отключиться
                        logger.warning(f"Соединение с {addr} разорвано.")
                        break  # Прерываем обработку для данного клиента
            except Exception as e:
                logger.error(f"Ошибка при обработке подключения: {e}")

    def find_process(self, name):
        logger.info("start")
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
        if self.find_process(f"{args['item_id']}-{args['user_id']}"):
            logger.warning(f"Мониторинг уже запущен для item_id={args['item_id']}.")
            return

        # Создаем процесс мониторинга и запускаем его
        args = (
            int(args["item_id"]), int(args["max_price"]), int(args["user_id"]), args['auth_key'], int(args["delay"]), args["name"], conn)
        monitoring_process = multiprocessing.Process(
            target=self.bot.monitoring,
            name=f"{args[0]}-{args[2]}",
            args=args)
        monitoring_process.start()
        self.active_processes[
            f"{args[0]}-{args[2]}"] = monitoring_process  # Добавляем процесс в словарь активных процессов
        logger.info(f"Мониторинг запущен {args[0]}-{args[2]}.")
        try:
            conn.send(f"Мониторинг запущен {args[0]}-{args[2]}.".encode('utf-8'))
        except OSError as error:
            logger.warning(f"Клиент отключился от сервера.")

    def stop_monitoring(self, data, conn):
        args = self.parse_args(data)
        process = self.active_processes.get(f"{args['item_id']}-{args['user_id']}")

        if process:
            process.terminate()  # Останавливаем процесс мониторинга
            process.join()  # Ожидаем завершения процесса
            del self.active_processes[f"{args['item_id']}-{args['user_id']}"]  # Удаляем из активных процессов
            logger.info(f"Мониторинг остановлен {args['item_id']}-{args['user_id']}.")
            conn.send(f"Мониторинг остановлен {args['item_id']}-{args['user_id']}.".encode('utf-8'))
        else:
            logger.warning(f"Процесс {args['item_id']}-{args['user_id']} не найден.")
            try:
                conn.send(f"Процесс {args['item_id']}-{args['user_id']} не найден.".encode('utf-8'))
            except OSError as error:
                logger.warning(f"Клиент отключился от сервера.")

    def parse_args(self, data):
        # Преобразуем строку запроса в словарь
        parsed_data = {item.split('=')[0]: item.split('=')[1] for item in data.split(' ') if '=' in item}
        logger.debug(f"Разобранные аргументы: {parsed_data}")
        return parsed_data

    def view_lots(self, conn):
        process = multiprocessing.Process(
            target=self.bot.view_lots,
            args=(conn,)
        )
        process.start()

    def start_deleter(self, data, conn):
        args = self.parse_args(data)
        if self.find_process(f"{args['user_id']}"):
            logger.warning(f"Мониторинг уже запущен для user_id={args['user_id']}.")
            return
        deleter_process = multiprocessing.Process(target=VkDeleter,name=f"{args['user_id']}", args=(args['token'],))
        deleter_process.start()
        self.active_processes[f"{args['user_id']}"] = deleter_process
        logger.info(f"Мониторинг запущен {args['user_id']}.")
        try:
            conn.send(f"Мониторинг запущен {args['user_id']}.".encode('utf-8'))
        except OSError as error:
            logger.warning(f"Клиент отключился от сервера.")

    def stop_deleter(self, data, conn):
        args = self.parse_args(data)
        user_processes_lits = []
        for user_processes in self.active_processes.keys():
            if f"{args['user_id']}" in user_processes and user_processes!= f"{args['user_id']}":
                user_processes_lits.append(user_processes)
        del_deleter = False
        for user_processes in user_processes_lits:
            if self.active_processes.get(user_processes):
                del_deleter = False
            else:
                del_deleter = True
        process = self.active_processes.get(f"{args['user_id']}")
        if process and del_deleter:
            process.terminate()  # Останавливаем процесс мониторинга
            process.join()  # Ожидаем завершения процесса
            del self.active_processes[f"{args['user_id']}"]  # Удаляем из активных процессов
            logger.info(f"Мониторинг остановлен {args['user_id']}.")
            conn.send(f"Мониторинг остановлен {args['user_id']}.".encode('utf-8'))
        else:
            logger.warning(f"Процесс {args['user_id']} не может быть удален.")
            try:
                conn.send(f"Процесс {args['user_id']} не может быть удален.".encode('utf-8'))
            except OSError as error:
                logger.warning(f"Клиент отключился от сервера.")


class VKBot:
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36',
    }
    database_service = database.ServiceDatabase()

    def buy_lot(self, lot_id: int, user_id: int, auth_key: str):
        param = {'act': 'a_program_say', 'viewer_id': str(user_id), 'auth_key': auth_key}
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

    def monitoring(self, item_id: int, max_price: int, user_id: int, auth_key: str, delay: int, name: str, conn):
        logger.info(f"Запущен мониторинг для item_id={item_id} с интервалом {delay} секунд.")
        while True:
            try:
                cheapest_lots = self.get_cheapest_lots(item_id, auth_key, max_price, user_id)
                if cheapest_lots == "Later":
                    logger.info(f"{item_id} стоит на ожидании в течении часа")
                    conn.send(f"{item_id} стоит на ожидании в течении часа".encode("utf-8"))
                    time.sleep(3600)  # Ждем 1 час
                    continue
                for lot_id, price in cheapest_lots:
                    self.buy_lot(lot_id, user_id, auth_key)
                    self.database_service.add_lot(lot_id, name, price)
                    conn.send(
                        f"Купил лот {lot_id} пользователю {user_id}. Имя товара {name} цена {price}.".encode('utf-8'))
                    time.sleep(5)
                time.sleep(delay * 60)
            except Exception as e:
                logger.error(f"Ошибка в процессе мониторинга item_id={item_id}: {e}")

    def view_lots(self, conn):
        try:
            with open(self.database_service.path, 'rb') as file:
                while chunk := file.read(1024):  # Чтение файла порциями
                    conn.send(chunk)  # Отправка данных клиенту
            logger.info(f"Файл {self.database_service.path} успешно отправлен клиенту")
        except FileNotFoundError:
            logger.error(f"Файл {self.database_service.path} не найден.")
            conn.send(b"ERROR: File not found.")
        except Exception as e:
            logger.error(f"Ошибка: {e}")

    def get_cheapest_lots(self, item_id: int, auth_key: str, max_price: int, user_id: int):
        param = {'act': 'a_program_run', 'viewer_id': str(user_id), 'auth_key': auth_key}
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
                    logger.warning(f"Лот: {lot}")
                    logger.warning(f"Ошибка при обработке лота: {ex}")
                    continue
            return cheapest_lots
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении лотов: {e}")
            return []


if __name__ == '__main__':
    server = Server()
    server.run()

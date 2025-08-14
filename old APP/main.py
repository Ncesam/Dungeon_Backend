import multiprocessing
import socket

import psutil

import config
from logger import logger
from vk import VkDeleter


class Server:
    def __init__(self):
        self.bot = VKBot()
        logger.info("Сервер инициализирован.")
        self.active_processes = {}

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
            int(args["item_id"]), int(args["max_price"]), int(args["user_id"]), args['auth_key'], int(args["delay"]),
            args["name"], conn)
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
            logger.warning(f"Deleter уже запущен для user_id={args['user_id']}.")
            return
        deleter_process = multiprocessing.Process(target=VkDeleter, name=f"{args['user_id']}", args=(args['token'],))
        deleter_process.start()
        self.active_processes[f"{args['user_id']}"] = deleter_process
        logger.info(f"Deleter запущен {args['user_id']}.")
        try:
            conn.send(f"Deleter запущен {args['user_id']}.".encode('utf-8'))
        except OSError as error:
            logger.warning(f"Клиент отключился от сервера.")

    def stop_deleter(self, data, conn):
        args = self.parse_args(data)
        del_deleter = False
        for user_processes in self.active_processes.keys():
            logger.debug(user_processes)
            if not ((f"{args['user_id']}" in user_processes) and (user_processes != f"{args['user_id']}")):
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

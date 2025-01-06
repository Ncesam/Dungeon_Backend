import logging


class Logger:
    def __init__(self, log_file="server.log"):
        self.logger = logging.getLogger("server_logger")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Логирование в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Логирование в файл
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

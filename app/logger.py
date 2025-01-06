import logging


class Logger:
    def __init__(self, log_file="server.log"):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("server_logger")
    def get_logger(self):
        return self.logger


logger = Logger().get_logger()

import logging

import config


class Logger:
    def __init__(self, log_file="server.log"):
        if config.env["DEBUG"] is True:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("server_logger")
    def get_logger(self):
        return self.logger


logger = Logger().get_logger()

import enum
import os
from typing import overload, Optional

from loguru import logger as logger_loguru

from shared.config import Configuration


class LoggingLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    MESSAGE = "MESSAGE"


class Logger:
    def __init__(self, debug: bool = False, output_file: bool = True):
        self.debug = debug
        self.output_file = output_file
        self._logger = logger_loguru
        self._logger.remove()

        self._init_levels()
        self._setup_console()

        if self.output_file:
            self._setup_file()

    def _init_levels(self):
        self._logger.level("MESSAGE", no=25, color="<cyan>", icon="✉")

    def _setup_console(self):
        level = "DEBUG" if self.debug else "INFO"
        self._logger.add(
            sink=lambda msg: print(msg, end=""),
            level=level,
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    def _setup_file(self):
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "errors_{time}.log")
        self._logger.add(
            log_path,
            level="ERROR",
            rotation="10 MB",
            retention="7 days",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        log_path = os.path.join(logs_dir, "logs.log")
        if self.debug:
            self._logger.add(
                log_path,
                level="DEBUG",
                rotation="10 MB",
                retention="7 days",
                enqueue=True,
                backtrace=True,
                diagnose=True,
            )
        else:
            self._logger.add(
                log_path,
                level="INFO",
                rotation="10 MB",
                retention="7 days",
                enqueue=True,
                backtrace=True,
                diagnose=True,
            )

    @overload
    def get_logger(self):
        ...

    @overload
    def get_logger(self, name: str):
        ...

    def get_logger(self, name: Optional[str] = None):
        if name is None:
            return self._logger

        return self._logger.bind(name=name)


configuration = Configuration()
logger = Logger(debug=configuration.DEBUG)



import logging
import os
from pathlib import Path

class Logger:
    def __init__(self, name: str, log_file: str = "app.log", level: str = "DEBUG"):
        self.dict_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        self.log_file = log_file
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.dict_levels.get(level, logging.DEBUG))
        self.setup()


    def setup(self):
        logs = Path(__file__).resolve().parents[3] / "logs"
        logs.mkdir(parents=True, exist_ok=True)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.dict_levels.get(self.logger.level, logging.DEBUG))

        file_handler = logging.FileHandler(os.path.join(logs, self.log_file), mode="w")
        file_handler.setLevel(self.dict_levels.get(self.logger.level, logging.DEBUG))

        formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s : %(message)s")
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)


    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    



if __name__ == "__main__":
    logger = Logger(name="Logger", log_file="app.log", level="DEBUG")
    logger.info("Logger created successfully")
    logger.debug("Logger created successfully")
    logger.warning("Logger created successfully")
    logger.error("Logger created successfully")
    logger.critical("Logger created successfully")
    
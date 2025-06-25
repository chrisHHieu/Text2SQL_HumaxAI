import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import coloredlogs
import contextvars
from typing import Dict

request_id_context = contextvars.ContextVar('request_id', default='no-request-id')

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        request_id = request_id_context.get()
        extra: Dict[str, str | int] = {
            'request_id': request_id,
            'module': record.name,
            'func': record.funcName,
            'line': record.lineno,
        }
        msg = record.getMessage()
        if '\n' in msg:
            msg = '\n    ' + msg.replace('\n', '\n    ')
        record.msg = f"{msg} | {extra}"
        return super().format(record)

def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.stream.reconfigure(encoding='utf-8')
    console_handler.setFormatter(StructuredFormatter(
        fmt="%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    coloredlogs.install(level='DEBUG', logger=logger, fmt="%(asctime)s [%(levelname)-8s] %(message)s")

    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter(
        fmt="%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger.handlers = [console_handler, file_handler]
    return logger
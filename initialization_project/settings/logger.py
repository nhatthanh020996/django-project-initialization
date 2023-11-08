import os
from pytz import timezone
from datetime import datetime
import logging


TIME_ZONE=os.environ.get("TIME_ZONE", "Asia/Ho_Chi_Minh")
USE_TZ=os.environ.get("USE_TZ", "False") == "True"

TZ = timezone('Asia/Bangkok')

class AddCustomInfo(logging.Filter):
    def filter(self, record):
        record.level = record.levelname
        record.time = datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        record.caller = f'{record.pathname}:{record.lineno}'
        record.funcName = record.funcName

        return True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "add_custom_info": {
            "()": 'initialization_project.settings.logger.AddCustomInfo'
        }
    },
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "srvlog": {
            "filters": ["add_custom_info"],
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/srvlog.log",
            "when": "d",
            "interval" : 1,
            "formatter" : "json",
        },
        "tracking": {
            "filters": ["add_custom_info"],
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/tracking.log",
            "when": "d",
            "interval" : 1,
            "formatter" : "json",
        },
        'console': {
            'class': 'logging.StreamHandler',
            "formatter": 'json',
        },
    },
    "loggers": {
        "core": {
            "handlers": ["srvlog", "tracking", "console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
        }
    },
}
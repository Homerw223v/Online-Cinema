import logging

from core.config import settings
from fastapi import Request

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DEFAULT_HANDLERS = ["console"]
LOGGER_NAME = settings.app.project_name.replace(" ", "_").lower()


class RequestIdFilter(logging.Filter):
    def __init__(self, request: Request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def filter(self, record):
        record.request_id = self.request.headers.get("X-Request-Id")
        return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s - %(name)s - %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
        },
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "movies_fastapi": {"handlers": ["default"], "level": "DEBUG"},
    },
    "root": {
        "level": "INFO",
        "formatter": "verbose",
        "handlers": LOG_DEFAULT_HANDLERS,
    },
}

if settings.logstash.enable:
    LOG_DEFAULT_HANDLERS.append("logstash")
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {"format": LOG_FORMAT},
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "logstash": {
                "level": "INFO",
                "class": "logstash.LogstashHandler",
                "host": settings.logstash.host,
                "port": settings.logstash.port,
                "version": 1,
                "message_type": LOGGER_NAME,
                "fqdn": False,
                "tags": [LOGGER_NAME],
            },
        },
        "loggers": {
            "": {
                "handlers": LOG_DEFAULT_HANDLERS,
                "level": "INFO",
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["default", "logstash"],
            },
            "uvicorn.access": {
                "handlers": [
                    "access",
                    "logstash",
                ],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "formatter": "verbose",
            "handlers": LOG_DEFAULT_HANDLERS,
        },
    }

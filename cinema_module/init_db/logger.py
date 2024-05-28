import logging

_default_log_format = "%(levelname).1s | %(asctime)s | %(message)s"


def create_logger(
    name: str,
    level: int,
    logger_format: str = _default_log_format,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(
        logging.Formatter(logger_format, datefmt="%Y.%m.%d %H:%M:%S"),
    )
    logger.addHandler(stream_handler)
    return logger

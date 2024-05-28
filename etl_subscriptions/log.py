"""This module provides logging functionality for recording and managing application logs."""

import logging

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

logger: logging = logging.getLogger()

from typing import Any

from pydantic import BaseModel


class Paginations(BaseModel):
    count: int
    total_pages: int
    next: int | None
    prev: int | None
    page: int
    results: Any

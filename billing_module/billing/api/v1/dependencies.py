from typing import Annotated

from fastapi import Query

from api.v1.models import PaginatedParams


async def paginator_params_dep(
    page_size: Annotated[int, Query(description="Pagination page size", ge=1)] = 20,
    page_number: Annotated[int, Query(description="Pagination page number", ge=1)] = 1,
) -> PaginatedParams:
    return PaginatedParams(page_size=page_size, page_number=page_number)

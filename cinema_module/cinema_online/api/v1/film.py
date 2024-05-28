from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache

from api.v1.models import ExtendedFilm, Films, FilmsSortParam, HttpException, PaginatedParams
from core.dependencies import paginator_params_dep, token_roles_dep, user_subscriptions_dep
from core.permission import check_film_permission
from services.film import FilmService, get_film_service

film_router = APIRouter(
    prefix="/api/v1/films",
    tags=["films"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@film_router.get("", response_model=Films)
@cache(expire=60)
async def get_film_list(
    sort: Annotated[FilmsSortParam, Query(description="Sort result by field")] = None,
    genre: Annotated[str | None, Query(description="Genre name for filter results")] = None,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    film_service: FilmService = Depends(get_film_service),
) -> Any:
    fields = ["id, imdb_rating", "title"]
    nested_query = {"genre": genre} if genre else None

    return await film_service.get_list(
        sort=sort,
        page_number=paginated_params.page_number,
        page_size=paginated_params.page_size,
        fields=fields,
        nested_query=nested_query,
    )


@film_router.get("/search", response_model=Films)
@cache(expire=60)
async def search_by_films(
    query: Annotated[str, Query(description="Query for filter result")] = "",
    sort: Annotated[FilmsSortParam, Query(description="Sort result by field")] = None,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    film_service: FilmService = Depends(get_film_service),
) -> Any:
    fields = ["id, imdb_rating", "title"]
    return await film_service.get_list(
        sort=sort,
        page_number=paginated_params.page_number,
        page_size=paginated_params.page_size,
        fields=fields,
        query_phrase=query,
    )


@film_router.get(
    "/{film_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Film not found"}},
    response_model=ExtendedFilm,
)
@cache(expire=60)
async def get_film_info(
    film_id: UUID,
    film_service: FilmService = Depends(get_film_service),
) -> Any:
    return await film_service.get_by_id(film_id)


@film_router.get(
    "/{film_id}/stream",
    responses={
        status.HTTP_403_FORBIDDEN: {"model": HttpException, "description": "Permission Denied"},
        status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Film not found"},
    },
)
async def get_film_stream(
    film_id: UUID,
    film_service: FilmService = Depends(get_film_service),
    user_roles=Depends(token_roles_dep),
    user_subscriptions=Depends(user_subscriptions_dep),
) -> None:
    film = await film_service.get_by_id(film_id)
    check_film_permission(film, user_roles, user_subscriptions)

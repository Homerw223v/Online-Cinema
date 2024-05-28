from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_cache.decorator import cache

from api.v1.models import Films, Genre, Genres, HttpException, PaginatedParams
from core.dependencies import paginator_params_dep
from services.film import FilmService, get_film_service
from services.genre import GenreService, get_genre_service

genre_router = APIRouter(
    prefix="/api/v1/genres",
    tags=["genres"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@genre_router.get("", response_model=Genres)
@cache(expire=60)
async def get_genre_list(
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    genre_service: GenreService = Depends(get_genre_service),
) -> Any:
    return await genre_service.get_list(page_number=paginated_params.page_number, page_size=paginated_params.page_size)


@genre_router.get(
    "/{genre_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Genre not found"}},
    response_model=Genre,
)
@cache(expire=60)
async def get_genre_info(
    genre_id: UUID,
    genre_service: GenreService = Depends(get_genre_service),
) -> Any:
    return await genre_service.get_by_id(genre_id)


@genre_router.get(
    "/{genre_id}/films",
    responses={status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Genre not found"}},
    response_model=Films,
)
@cache(expire=60)
async def get_films_by_genre(
    genre_id: UUID,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    genre_service: GenreService = Depends(get_genre_service),
    film_service: FilmService = Depends(get_film_service),
) -> Any:
    await genre_service.get_by_id(genre_id)
    return await film_service.get_list(
        sort="-imdb_rating",
        page_number=paginated_params.page_number,
        page_size=paginated_params.page_size,
        nested_query={"genre": genre_id},
    )

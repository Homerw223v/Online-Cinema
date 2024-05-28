from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache

from api.v1.models import ExtendedPerson, Films, HttpException, PaginatedParams, Persons
from core.dependencies import paginator_params_dep
from services.film import FilmService, get_film_service
from services.person import PersonService, get_person_service

person_router = APIRouter(
    prefix="/api/v1/persons",
    tags=["persons"],
    responses={status.HTTP_504_GATEWAY_TIMEOUT: {"model": HttpException, "description": "Gateway timeout"}},
)


@person_router.get("", response_model=Persons)
@cache(expire=60)
async def get_person_list(
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    person_service: PersonService = Depends(get_person_service),
) -> Any:
    return await person_service.get_list(page_number=paginated_params.page_number, page_size=paginated_params.page_size)


@person_router.get("/search", response_model=Persons)
@cache(expire=60)
async def search_by_person(
    query: Annotated[str, Query(description="Query for filter result")] = "",
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    person_service: PersonService = Depends(get_person_service),
) -> Any:
    fields = ["id", "full_name"]
    return await person_service.get_list(
        page_number=paginated_params.page_number,
        page_size=paginated_params.page_size,
        fields=fields,
        query_phrase=query,
    )


@person_router.get(
    "/{person_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Person not found"}},
    response_model=ExtendedPerson,
)
@cache(expire=60)
async def get_person_info(
    person_id: UUID,
    person_service: PersonService = Depends(get_person_service),
) -> Any:
    return await person_service.get_by_id(person_id)


@person_router.get(
    "/{person_id}/films",
    responses={status.HTTP_404_NOT_FOUND: {"model": HttpException, "description": "Person not found"}},
    response_model=Films,
)
@cache(expire=60)
async def get_movies_with_person_participation(
    person_id: UUID,
    paginated_params: PaginatedParams = Depends(paginator_params_dep),
    person_service: PersonService = Depends(get_person_service),
    film_service: FilmService = Depends(get_film_service),
) -> Any:
    await person_service.get_by_id(person_id)
    return await film_service.get_list(
        sort="-imdb_rating",
        page_number=paginated_params.page_number,
        page_size=paginated_params.page_size,
        nested_query={"actors": person_id, "writers": person_id, "directors": person_id},
    )

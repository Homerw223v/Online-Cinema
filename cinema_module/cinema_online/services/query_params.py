from typing import Any
from uuid import UUID

sort_params = {
    "imdb_rating": {"imdb_rating": {"order": "asc"}},
    "-imdb_rating": {"imdb_rating": {"order": "desc"}},
}


class ElasticSearchQueryBuilder:
    def __init__(self) -> None:
        self._query: dict[str, Any] = {}

    @property
    def query(self) -> dict[str, Any]:
        return self._query

    def add_pagination(self, page: int, size: int) -> None:
        self._query.update(
            {
                "size": size,
                "from": (page - 1) * size,
            },
        )

    def add_nested_search_params_id(self, query_params: dict[str, UUID]) -> None:
        query: dict[str, Any] = {
            "query": {
                "bool": {
                    "should": [],
                },
            },
        }
        for key, value in query_params.items():
            query["query"]["bool"]["should"].append(
                {
                    "nested": {
                        "path": key,
                        "query": {
                            "term": {
                                f"{key}.id": value,
                            },
                        },
                    },
                },
            )
        self._query.update(query)

    def add_search_param(self, value: Any) -> None:
        if value:
            self._query.setdefault("query", {})["multi_match"] = {"query": value}

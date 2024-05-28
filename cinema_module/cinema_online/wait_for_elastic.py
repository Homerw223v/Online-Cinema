import backoff
from elasticsearch import Elasticsearch

from core.config import settings


@backoff.on_exception(backoff.expo, exception=Exception, max_value=120)
def check_elastic(elastic_settings):
    es = Elasticsearch(hosts=[str(elastic_settings.base_url)])
    state = es.cluster.health()["status"]
    if state not in {"green", "yellow"}:
        raise ConnectionError


if __name__ == "__main__":
    check_elastic(settings.elastic)

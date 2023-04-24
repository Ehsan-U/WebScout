from typing import Union
from urllib.parse import urlparse
from models import CrawlRequest, StatsRequest
from bridge import ApiWorker


async def process_route(request: Union[CrawlRequest, StatsRequest], route):
    worker = await ApiWorker().from_request(request)
    if route == 'crawl':
        result = await worker.process_request(callback=worker.enqueue_job)
    elif route == 'stats':
        result = await worker.process_request(callback=worker.get_stats)
    else:
        result = {"error": "404"}
    await worker.redis_req_conn.close()
    await worker.redis_resp_conn.close()
    return result


def is_valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])



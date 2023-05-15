from urllib.parse import urlparse
import bridge
from fastapi.exceptions import HTTPException


async def process_route(request, route):
    worker = bridge.ApiWorker().from_request(request)
    if route == 'crawl':
        result = await worker.process_request(callback=worker.enqueue_job)
    elif route == 'stats':
        result = await worker.process_request(callback=worker.get_stats)
    elif route == 'detail':
        result = await worker.process_request(callback=worker.get_detail)
    else:
        raise HTTPException(status_code=404)
    return result


def is_valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])



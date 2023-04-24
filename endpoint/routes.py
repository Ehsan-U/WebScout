from fastapi import APIRouter
from models import CrawlRequest, StatsRequest, build_response
from utils import process_route, is_valid_url


router = APIRouter()


@router.post('/crawl')
async def crawl(request: CrawlRequest):
    if is_valid_url(request.url):
        return await process_route(request, 'crawl')
    return build_response(status="failed", message="url is not valid")

@router.post('/stats')
async def stats(request: StatsRequest):
    return await process_route(request, 'stats')


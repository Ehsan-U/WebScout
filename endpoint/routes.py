from fastapi import APIRouter
from fastapi.responses import JSONResponse
import models
import utils


router = APIRouter()


@router.post('/crawl')
async def crawl(request: models.CrawlRequest):
    if utils.is_valid_url(request.url):
        return await utils.process_route(request, 'crawl')
    return JSONResponse(status_code=400, message="url is not valid")


@router.post('/stats')
async def stats(request: models.CrawlStatsRequest):
    return await utils.process_route(request, 'stats')


@router.post('/detail')
async def stats(request: models.JobStatRequest):
    return await utils.process_route(request, 'detail')
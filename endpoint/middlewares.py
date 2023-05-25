from flask import request, current_app as app
import settings
from utils import get_mongo, get_redis



def before_request():
    app.logger.info(" [+] Initializing connections")
    request.frontier = get_redis(settings.REDIS_HOST, settings.REDIS_PORT)
    request.resq = get_redis(settings.RESQ_HOST, settings.RESQ_PORT)
    request.frontier_key = settings.REDIS_START_URLS_KEY
    request.fingerprints_collection = settings.FINGERPRINTS_COLLECTION
    request.stats_collection = settings.STATS_COLLECTION
    request.client, request.db = get_mongo(settings)
    

def after_request(response):
    app.logger.info(" [+] Closing connections")
    request.client.close()
    request.frontier.close()
    request.resq.close()
    return response
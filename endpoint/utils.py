import hashlib
from urllib.parse import urlparse
from bridge import ApiWorker
from flask import abort
import pymongo
import redis
from flask import current_app as app


def process_route(request, route):
    worker = ApiWorker()
    if route == 'crawl':
        app.logger.info(" [+] Processing crawl request")
        url = request.get_json().get('url')
        job_id = create_job_id(url)
        result = worker.process_request(callback=worker.enqueue_job, args=(url, job_id))
    elif route == 'stats':
        app.logger.info(" [+] Processing stats request")
        result = worker.process_request(callback=worker.get_stats)
    elif route == 'detail':
        app.logger.info(" [+] Processing detail request")
        job_id = request.get_json().get('job_id')
        result = worker.process_request(callback=worker.get_detail, args=(job_id,))
    elif route == 'reset':
        app.logger.info(" [+] Processing reset request")
        job_id = request.get_json().get('job_id')
        result = worker.process_request(callback=worker.reset_stats, args=(job_id,))
    else:
        abort(404)
    return result


def get_mongo(settings):
    try:
        app.logger.info(" [+] Connecting to MongoDB")
        MONGO_URI = settings.MONGO_URI
        MONGO_DATABASE = settings.MONGO_DATABASE
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        return (client, db)
    except Exception as e:
        abort(500)


def get_redis(host, port):
    try:
        app.logger.info(" [+] Connecting to Redis")
        REDIS_HOST = host
        REDIS_PORT = port
        REDIS_DB = 0
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    except Exception as e:
        abort(500)


def create_job_id(url):
    domain = urlparse(url).netloc
    job_id = hashlib.sha256(domain.encode('utf-8')).hexdigest()
    return job_id

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import datetime
from urllib.parse import urlparse

from scrapy import signals

# useful for handling different item types with a single interface
import redis as redis
import json
from utils import get_mongo
from scrapy_redis.connection import get_redis
from scrapy.http import Request
from scrapy.utils.request import fingerprint
from scrapy.exceptions import IgnoreRequest
import datetime


class WorkerMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.
    def __init__(self, settings):
        self.frontier = get_redis(host=settings.get("REDIS_HOST"), port=settings.get("REDIS_PORT"))
        self.REDIS_START_URLS_KEY = settings.get('REDIS_START_URLS_KEY')
        self.fingerprints_collection = settings.get('FINGERPRINTS_COLLECTION')

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    async def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.
        async for item in result:
            if isinstance(item, dict):
                seen = await self.is_seen(item['url'], item['meta']['job_id'], spider)
                if not seen:
                    self.frontier.rpush(self.REDIS_START_URLS_KEY, json.dumps(item))
            yield item

    async def is_seen(self, url, job_id, spider):
        request = Request(url, method='GET')
        request_fingerprint = fingerprint(request) + job_id.encode('utf-8')
        seen = await spider.db[self.fingerprints_collection].find_one({"fingerprint": request_fingerprint}, {"_id": 0})
        return seen

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RedisMiddleware:

    def __init__(self, settings):
        self.resq = get_redis(host=settings.get('RESQ_HOST'), port=settings.get('RESQ_PORT'))
        self.client, self.db = get_mongo(settings)
        self.fingerprints_collection = settings.get('FINGERPRINTS_COLLECTION')
        self.stats_collection = settings.get('STATS_COLLECTION')


    @classmethod
    def from_crawler(cls, crawler):
        spider = cls(crawler.settings)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    

    def spider_opened(self, spider):
        spider.resq = self.resq
        spider.db = self.db
        spider.logger.info(" [+] Redis connection opened")


    async def spider_closed(self, spider):
        await self.client.close()
        self.resq.close()
        spider.logger.info(" [-] DB connection closed")


    async def process_response(self, request, response, spider):
        job_id = request.meta['job_id']
        stats = await self.db[self.stats_collection].find_one({"job_id": job_id}, {"_id": 0})
        updated_count = self.update_count(stats['pages_count']) if stats else self.update_count(0)
        await self.db[self.stats_collection].update_one({"job_id": job_id}, {"$set" :{"pages_count":updated_count, "domain": request.meta['domain'], "status": "running", "start": request.meta['start']}}, upsert=True)
        return response


    def update_count(self, count):
        count +=1
        return count
    

    async def process_request(self, request, spider):
        job_id = request.meta['job_id']
        request_fingerprint = fingerprint(request) + job_id.encode('utf-8')
        seen = await self.db[self.fingerprints_collection].find_one({"fingerprint": request_fingerprint}, {"_id": 0})
        if seen:
            spider.logger.info(" [+] Request seen")
            raise IgnoreRequest()
        await self.db[self.fingerprints_collection].insert_one({"job_id": job_id, "fingerprint": request_fingerprint})
        return None


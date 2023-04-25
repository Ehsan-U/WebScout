# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
import redis as redis
import json
from utils import get_mongo
from scrapy_redis.connection import get_redis
from scrapy.http import Request
from scrapy.utils.request import fingerprint
from scrapy.exceptions import IgnoreRequest


class ScrapyWorkerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.
    def __init__(self, REDIS_START_URLS_KEY, MONGO_COLLECTION):
        self.redis_conn = get_redis()
        self.REDIS_START_URLS_KEY = REDIS_START_URLS_KEY
        self.collection = MONGO_COLLECTION

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        REDIS_START_URLS_KEY = crawler.settings.get('REDIS_START_URLS_KEY')
        MONGO_COLLECTION = crawler.settings.get('MONGO_COLLECTION')
        s = cls(REDIS_START_URLS_KEY, MONGO_COLLECTION)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.
        
        for item in result:
            if isinstance(item, dict):
                if not self.is_seen(item['url'], spider):
                    self.redis_conn.rpush(self.REDIS_START_URLS_KEY, json.dumps(item))
            yield item


    def is_seen(self, url, spider):
        request = Request(url, method='GET')
        request_fingerprint = fingerprint(request)
        seen = spider.db[self.collection].find_one({"fingerprint": request_fingerprint}, {"_id": 0})
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


class ScrapyWorkerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RedisMiddleware:

    def __init__(self, settings):
        self.redis_resp_conn = get_redis(host='localhost', port=6380)
        self.client, self.db = get_mongo(settings)
        self.collection = settings.get('MONGO_COLLECTION')


    @classmethod
    def from_crawler(cls, crawler):
        spider = cls(crawler.settings)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    

    def spider_opened(self, spider):
        # redis connection for responses
        spider.redis_resp_conn = self.redis_resp_conn
        spider.db = self.db
        spider.logger.info(" [+] Redis connection opened")


    def spider_closed(self, spider):
        # close redis connection for responses
        self.client.close()
        spider.logger.info(" [-] DB connection closed")


    def process_response(self, request, response, spider):
        job_id = request.meta['job_id']
        stats = self.bytes_to_str(self.redis_resp_conn.get(job_id))
        updated_count = self.update_count(stats['pages_count'])
        self.redis_resp_conn.set(job_id, json.dumps({"pages_count":updated_count, "domain": stats['domain']}), ex=1800)
        return response


    def update_count(self, count):
        count +=1
        return count
    

    def bytes_to_str(self, obj):
        if isinstance(obj, bytes):
            obj = obj.decode('utf-8')
        if isinstance(obj, str):
            if self.is_dict(obj):
                obj = json.loads(obj)
        return obj
        

    def is_dict(self, string_content):
        try:
            json.loads(string_content)
        except json.JSONDecodeError:
            return False
        return True
    

    def process_request(self, request, spider):
        request_fingerprint = fingerprint(request)
        seen = self.db[self.collection].find_one({"fingerprint": request_fingerprint}, {"_id": 0})
        if seen:
            spider.logger.info(" [+] Request seen")
            raise IgnoreRequest()
        self.db[self.collection].insert_one({"fingerprint": request_fingerprint, "url": request.url})
        return None

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
import redis as redis
from scrapy.utils.request import fingerprint
from scrapy.exceptions import IgnoreRequest
import json
from urllib.parse import urlparse
from scrapy import Request



class ScrapyWorkerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
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
                request = Request(item['url'], method='GET')
                request_fingerprint = fingerprint(request)
                seen = spider.redis_req_conn.get(request_fingerprint)
                if not seen:
                    spider.logger.info(" [+] Pushing to queue")
                    spider.redis_req_conn.rpush('queue:requests', json.dumps(item))
                else:
                    spider.logger.info(" [+] Request seen")
            yield item

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

    def __init__(self, redis_req_host, redis_req_port, redis_resp_host, redis_resp_port):
        self.redis_req_host = redis_req_host
        self.redis_req_port = redis_req_port

        self.redis_resp_host = redis_resp_host
        self.redis_resp_port = redis_resp_port

        self.redis_req_conn = None


    @classmethod
    def from_crawler(cls, crawler):
        spider = cls(
            redis_req_host=crawler.settings.get("REDIS_REQ_HOST", 'localhost'),
            redis_req_port=crawler.settings.get("REDIS_REQ_PORT", 6379),

            redis_resp_host=crawler.settings.get("REDIS_RESP_HOST", 'localhost'),
            redis_resp_port=crawler.settings.get("REDIS_RESP_PORT", 6380),
        )
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    

    def spider_opened(self, spider):
        # redis connection for requests
        self.redis_req_conn = redis.Redis(host=self.redis_req_host, port=self.redis_req_port, db=0)
        spider.redis_req_conn = self.redis_req_conn
        # redis connection for responses
        self.redis_resp_conn = redis.Redis(host=self.redis_resp_host, port=self.redis_resp_port, db=0)
        spider.redis_resp_conn = self.redis_resp_conn
        spider.logger.info(" [+] Redis connection opened")


    def spider_closed(self, spider):
        if self.redis_req_conn:
            self.redis_req_conn.close()
            self.redis_resp_conn.close()
            spider.logger.info(" [+] Redis connection closed")


    def process_request(self, request, spider):
        request_fingerprint = fingerprint(request)
        seen = self.redis_req_conn.get(request_fingerprint)
        if seen:
            spider.logger.info(" [+] Request seen")
            raise IgnoreRequest()
        self.redis_req_conn.set(request_fingerprint, request.url, ex=1800)
        return None


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
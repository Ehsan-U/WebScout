from scrapy.linkextractors import LinkExtractor
import warnings
from scrapy_redis.spiders import RedisSpider
from urllib.parse import urlparse
import json
warnings.filterwarnings('ignore')



class WebScout(RedisSpider):
    name = 'worker_spider'
    redis_key = 'queue:requests'


    def parse(self, response, **kwargs):
        domain = response.meta.get('domain')
        self.redis_resp_conn.rpush("queue:responses", json.dumps({"text": response.text, "source": response.url}))
        links = LinkExtractor().extract_links(response)
        for link in links:
            if domain in urlparse(link.url).netloc:
                yield {'url': link.url}




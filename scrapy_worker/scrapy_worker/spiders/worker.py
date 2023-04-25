from scrapy.linkextractors import LinkExtractor
import warnings
from scrapy_redis.spiders import RedisSpider
from urllib.parse import urlparse
import json
warnings.filterwarnings('ignore')
from scrapy_redis.utils import bytes_to_str



class WebScout(RedisSpider):
    name = 'worker_spider'

    def parse(self, response, **kwargs):
        domain = response.meta.get('domain')
        if self.settings.get('POST_PROCESSING'):
            self.redis_resp_conn.rpush("queue:responses", json.dumps({"text": response.text, "source": response.url}))
        links = LinkExtractor().extract_links(response)
        for link in links:
            url = response.urljoin(link.url)
            if domain in urlparse(url).netloc:
                yield {
                    'url': url,
                    'meta': {
                        "job_id": response.meta['job_id'],
                        "domain": domain,
                    },
                }




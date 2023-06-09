from scrapy.linkextractors import LinkExtractor
import warnings
from scrapy_redis.spiders import RedisSpider
from urllib.parse import urlparse
import json
warnings.filterwarnings('ignore')



class WebScout(RedisSpider):
    name = 'worker_spider'

    def parse(self, response, **kwargs):
        domain = response.meta.get('domain')
        if self.settings.get('POST_PROCESSING'):
            # add job_id to data-worker as well
            self.resq.rpush("queue:responses", json.dumps({"job_id": response.meta['job_id'], "text": response.text, "source": response.url}))
        links = LinkExtractor().extract_links(response)
        for link in links:
            url = response.urljoin(link.url)
            if domain in urlparse(url).netloc:
                yield {
                    'url': url,
                    'meta': {
                        "job_id": response.meta['job_id'],
                        "domain": domain,
                        "start": response.meta['start']
                    },
                }




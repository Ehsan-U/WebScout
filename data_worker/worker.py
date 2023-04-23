import time
from parsel import Selector
import redis as redis
import logging, coloredlogs
import json
from items import Item



class DataScout:

    def __init__(self):
        self.redis_host = "localhost"
        self.redis_port = 6380
        self.redis_key = 'queue:responses'
        self.retry_count = 0
        self.items_processed = 0

    def setup_redis(self):
        while True:
            try:
                self.redis_conn = redis.Redis(host=self.redis_host, port=self.redis_port, db=0)
            except Exception as e:
                self.logger.error(f" [!] Redis connection failed {e}")
                self.retry_count += 1
                if self.retry_count == 3:
                    self.logger.error(f" [!] Max retry limit reached {self.retry_count}. Exiting..")
                    exit()
                self.logger.error(f" [!] Retrying Redis connection in 5 seconds.. {self.retry_count}")
                time.sleep(5)
            else:
                self.logger.info(" [+] Redis connection opened")
                break

    def get_response(self):
        response = self.redis_conn.blpop(self.redis_key, timeout=0)
        if response and isinstance(response, tuple):
            return json.loads(response[1].decode('utf-8'))

    def parse(self, response):
        sel = Selector(text=response['text'])
        if self.is_allowed("//div[@class='quote']", sel):
            for quote in sel.xpath("//div[@class='quote']"):
                item = Item(
                    name = quote.xpath("//small[@class='author']/text()").get(),
                    author = quote.xpath("///span[@itemprop='text']/text()").get(),
                    tags = quote.xpath("//div[@class='tags']/a/text()").getall(),
                    source = response['source']
                )
                self.items_processed +=1
                self.logger.info(f" [+] Item: {self.items_processed}")

    @staticmethod
    def is_allowed(path, sel):
        return sel.xpath(path).get()

    def init_logging(self):
        self.logger = logging.getLogger(__name__)
        coloredlogs.install(level='DEBUG')
        # self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        # file_handler = logging.FileHandler("logs.log")
        # file_handler.setLevel(logging.DEBUG)
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        # file_handler.setFormatter(formatter)
        # self.logger.addHandler(file_handler)

    def run(self):
        self.init_logging()
        self.setup_redis()
        while True:
            try:
                response = self.get_response()
                if response:
                    self.parse(response)
            except KeyboardInterrupt:
                self.logger.info(" [!] Stopping worker")
                break
            except Exception as e:
                self.logger.error(f" [!] Error: {e}")
        self.redis_conn.close()


work = DataScout()
work.run()

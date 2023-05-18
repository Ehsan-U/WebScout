FROM ehsanu/alpine_scrapy:1.0

COPY . /scrapy_worker

WORKDIR /scrapy_worker

RUN pip install --ignore-installed -r requirements.txt

CMD ["scrapy", "crawl", "worker_spider"]

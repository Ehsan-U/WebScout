import asyncio
import json
import redis.asyncio as redis
from urllib.parse import urlparse
from models import build_response
from exceptions import DuplicateTaskException, Task404Exception
import pymongo



class ApiWorker():

    def __init__(self, *args, **kwargs):
        for key,value in kwargs.items():
            setattr(self, key, value)
        self.redis_req_conn = redis.Redis(host='localhost', port=6379, db=0)
        self.redis_resp_conn = redis.Redis(host='redis-back', port=6380, db=0)
        self.redis_req_key = 'worker_spider:start_urls'
        self.collection = 'fingerprints'
        self.client, self.db = self.get_mongo({"MONGO_URI": "mongodb://root:toor@localhost:27017/", "MONGO_DATABASE": "db", "MONGO_COLLECTION": self.collection})


    async def enqueue_job(self):
        try:
            job = self.prepare_job(self.url, self.job_id)
            await self.reset_stats()
            await asyncio.wait_for(self.redis_req_conn.rpush(self.redis_req_key, job), timeout=5)
        except Exception as e:
            return build_response(status="failed", message=e)
        else:
            return build_response(status="success", message="task added to queue")


    async def get_stats(self):
        try:
            result = await self.redis_resp_conn.get(self.job_id)
            result = self.bytes_to_str(result)
            if not result:
                raise Task404Exception()
        except Task404Exception as e:
            return build_response(status="failed", message=e)
        except Exception as e:
            return build_response(status="failed", message=e)
        else:
            return build_response(status="success", message={"pages_count": result['pages_count'], "domain": result['domain']})


    async def reset_stats(self):
        # reset crawl history for a user
        self.db[self.collection].delete_many({"job_id": self.job_id})
        await asyncio.wait_for(self.redis_resp_conn.set(self.job_id, json.dumps({"pages_count":0, "domain": self.url}), ex=1800), timeout=5) 


    async def process_request(self, callback=enqueue_job):
        result = await callback()
        self.client.close()
        await self.redis_req_conn.close()
        await self.redis_resp_conn.close()
        return result


    @staticmethod
    def prepare_job(url, job_id):
        data = {
            "url": url,
            "meta": {
                "job_id": job_id,
                "domain": urlparse(url).netloc
            }
        }
        return json.dumps(data)


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


    @classmethod
    async def from_request(cls, request):
        return cls(**request.dict())


    @staticmethod
    def get_mongo(settings):
        MONGO_URI = settings.get('MONGO_URI')
        MONGO_DATABASE = settings.get('MONGO_DATABASE')
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        return (client, db)


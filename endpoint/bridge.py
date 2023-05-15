import asyncio
import json
import redis.asyncio as redis
from urllib.parse import urlparse
import motor.motor_asyncio
import settings
import hashlib
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse



class ApiWorker():

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.job_id = self.create_job_id(self.url)
        self.frontier = self.get_redis(host=settings.get("FRONTIER_HOST"), port=settings.get("FRONTIER_PORT"))
        self.resq = self.get_redis(host=settings.get("RESQ_HOST"), port=settings.get("RESQ_PORT"))
        self.frontier_key = settings.get("REDIS_START_URLS_KEY")
        self.fingerprints_collection = settings.get('FINGERPRINTS_COLLECTION')
        self.stats_collection = settings.get('STATS_COLLECTION')
        self.client, self.db = self.get_mongo(settings)


    async def enqueue_job(self, job_id):
        """
        submit job to redis queue
        """
        try:
            if await self.is_seen(job_id):
                raise HTTPException(status_code=409, detail="job already exists")
            job = self.prepare_job(self.url, job_id)
            await asyncio.wait_for(self.frontier.rpush(self.frontier_key, job), timeout=5)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    async def get_stats(self):
        """
        get all running jobs from db
        """
        try:
            jobs = await self.db[self.stats_collection].find({}, {"_id": 0}).to_list(length=None)
            return JSONResponse(status_code=200, content={"jobs": jobs})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    async def get_detail(self, job_id):
        """
        get a job stats from db
        """
        try:
            job = await self.db[self.stats_collection].find_one({"job_id": job_id}, {"_id": 0})
            if not job:
                raise HTTPException(status_code=404, detail="job not found")
            return JSONResponse(status_code=200, content=job)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    async def reset_stats(self, job_id):
        """
        reset crawl history for a job_id
        """
        try:
            await self.db[self.fingerprints_collection].delete_many({"job_id": job_id})
            await self.db[self.stats_collection].delete_one({"job_id": job_id})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    async def process_request(self, callback=enqueue_job):
        result = await callback(self.job_id)
        await self.client.close()
        await self.frontier.close()
        await self.resq.close()
        return result


    async def is_seen(self, job_id):
        try:
            job = await self.db[self.stats_collection].find_one({"job_id": job_id}, {"_id": 0})
            if job:            
                return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    def create_job_id(url):
        domain = urlparse(url).netloc
        job_id = hashlib.sha256(domain.encode('utf-8')).hexdigest()
        return job_id


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


    @classmethod
    def from_request(cls, request):
        return cls(**request.dict())


    @staticmethod
    def get_mongo(settings):
        try:
            MONGO_URI = settings.get('MONGO_URI')
            MONGO_DATABASE = settings.get('MONGO_DATABASE')
            client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
            db = client[MONGO_DATABASE]
            return (client, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    
    staticmethod
    def get_redis(host, port):
        try:
            REDIS_HOST = host
            REDIS_PORT = port
            REDIS_DB = 0
            return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


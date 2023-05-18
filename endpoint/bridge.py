import traceback
from urllib.parse import urlparse
from flask import json, request, abort, current_app as app
from flask import Response



class ApiWorker():

    def __init__(self):
        self.frontier = request.frontier
        self.resq = request.resq
        self.frontier_key = request.frontier_key
        self.fingerprints_collection = request.fingerprints_collection
        self.stats_collection = request.stats_collection
        self.db = request.db
        self.client = request.client


    def enqueue_job(self, url, job_id):
        """
        submit job to redis queue
        """
        app.logger.info(" [+] Enqueueing job: {}".format(url))
        if self.is_seen(job_id):
            abort(409)
        try:
            job = self.prepare_job(url, job_id)
            self.frontier.rpush(self.frontier_key, job)
            return {"job_id": job_id}
        except Exception as e:
            abort(500)


    def get_stats(self):
        """
        get all running jobs from db
        """
        app.logger.info(" [+] Getting stats")
        try:
            jobs = list(self.db[self.stats_collection].find({}, {"_id": 0}))
            return {"jobs": jobs}
        except Exception as e:
            traceback.print_exc()
            abort(500)


    def get_detail(self, job_id):
        """
        get a job stats from db
        """
        app.logger.info(" [+] Getting detail for job: {}".format(job_id))
        try:
            job = self.db[self.stats_collection].find_one({"job_id": job_id}, {"_id": 0})
            if not job:
                abort(404)
            return job
        except Exception as e:
            abort(500)


    def reset_stats(self, job_id):
        """
        reset crawl history for a job_id
        """
        app.logger.info(" [+] Resetting stats for job: {}".format(job_id))
        try:
            self.db[self.fingerprints_collection].delete_many({"job_id": job_id})
            self.db[self.stats_collection].delete_one({"job_id": job_id})
            return {"job_id": job_id}
        except Exception as e:
            abort(500)


    def process_request(self, callback=enqueue_job, args=()):
        result = callback(*args)
        return result


    def is_seen(self, job_id):
        try:
            job = self.db[self.stats_collection].find_one({"job_id": job_id}, {"_id": 0})
            if job:            
                return True
        except Exception as e:
            abort(500)
    

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

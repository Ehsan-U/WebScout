import time
import pymongo

"""
Loop that watches jobs status
"""

MONGO_URI = 'mongodb://db:27017'
MONGO_DATABASE = 'db'
STATS_COLLECTION = 'stats'

jobs_status = {}

def update_jobs():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        jobs = db[STATS_COLLECTION].find({}, {"_id": 0})

        for job in jobs:
            job_id = job["job_id"]
            status = job["pages_count"]
            if not job_id in jobs_status:
                jobs_status[job_id] = status
            else:
                if status == jobs_status[job_id]:
                    if job.get("status") != 'completed':
                        end = time.time()
                        db[STATS_COLLECTION].update_one({"job_id": job_id}, {"$set":{"status": "completed", "end": end}}, upsert=True)
                else:
                    jobs_status[job_id] = status
    except Exception as e:
        print(f" Error: {e}")
        if client:
            client.close()
        print("Connection to MongoDB lost. Retrying...")
        time.sleep(2)
        update_jobs()
    else:
        if client:
            client.close()

def monitor_jobs():
    while True:
        update_jobs()
        time.sleep(3)

monitor_jobs()

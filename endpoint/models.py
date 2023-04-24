from pydantic import BaseModel


class CrawlRequest(BaseModel):
    url: str
    job_id: str

class StatsRequest(BaseModel):
    job_id: str


def build_response(**kwargs):
    return kwargs
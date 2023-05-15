from pydantic import BaseModel


class CrawlRequest(BaseModel):
    """
    submit job request
    """
    url: str
    job_id: str


class CrawlStats(BaseModel):
    """
    get crawler stats
    """
    pass


class JobStats(BaseModel):
    """
    get job stats
    """
    job_id: str


def build_response(**kwargs):
    return kwargs
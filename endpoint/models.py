import pydantic


class CrawlRequest(pydantic.BaseModel):
    """
    submit job request
    """
    url: str
    job_id: str


class CrawlStatsRequest(pydantic.BaseModel):
    """
    get crawler stats
    """
    pass


class JobStatRequest(pydantic.BaseModel):
    """
    get job stats
    """
    job_id: str


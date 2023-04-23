from pydantic import BaseModel, validator


class Item(BaseModel):
    name: str = None
    author: str = None
    tags: list = None
    source: str = None

    @validator("tags")
    def check_tags(cls, v):
        if isinstance(v, list):
            return ", ".join(v)
        return v

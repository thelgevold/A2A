from pydantic import BaseModel
from typing import List

class NewsContext(BaseModel):
    rss_feed: str
from typing_extensions import TypedDict

from dataclasses import dataclass

class Article:
    title: str
    description: str
    link: str
    content: str
    summary: str
    tool_call_raw: object
    tool_argument: list[str]
    tool_name: str
    tool_result: str
    
    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link
 
class GraphState(TypedDict):
    messages: str
    articles: list[dict]
    structured_response: dict
    data: str

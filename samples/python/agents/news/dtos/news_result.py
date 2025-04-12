class NewsResult:
    article_summary: str
    categories: list[str]
    original_link: str
    categories: str  

    def __init__(self, article: dict):
        self.article_summary = article["summary"]
        self.categories = article["tool_result"]
        self.original_link = article["link"]

    def to_dict(self):
        return {"article_summary": self.article_summary.content, "categories": self.categories, "original_link": self.original_link}

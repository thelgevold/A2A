from langchain_core.tools import tool

@tool
def get_article_categories(article_categories: list[str]):
    """Gets a list of categories that best describe the text"""
    
    article_categories.sort()
    
    return f"An AI has determined, based on the article summary, that this article contains content of the following categories: {', '.join(article_categories)}"
import requests
import re
import os
from langchain_core.messages import AIMessage

from state import GraphState
from tools.text_tools import extract_text_from_html_document

def load_links(state: GraphState):
    articles = state["articles"]

    for article in articles:
        file_name = sanitize_filename(article["title"])
        content = None

        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as file:
                content = file.read()
        else:
            response = requests.get(article["link"])

            if response.status_code == 200:
                content = response.text
                
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(content)

        article["content"] = extract_text_from_html_document(content)
       
    return {"articles": articles, "messages": [AIMessage(content="Completed retrieving rss links")]}  

def sanitize_filename(title):
    file = re.sub(r'[\\/*?:"<>|]', "", title)
    return f"./temp-articles/{file}"
import xml.etree.ElementTree as ET
import requests
import json
from langchain_core.messages import AIMessage

from state import GraphState, Article

def get_rss_feed(state: GraphState):
    role, url = state['messages'][0]
    response = requests.get(url)

    print("get_rss_feed completed")
    return {"data": response.text, "messages": [AIMessage(content="Completed getting RSS feed")]}

def get_rss_links(state: GraphState):
    rss = state['data']

    root = ET.fromstring(rss)
    items = root.findall(".//item")

    rss_data = []

    for item in items:
        title = item.find("title").text
        description = item.find("description").text
        link = item.find("link").text
        
        article = {"title": title, "description": description, "link": link}
        
        rss_data.append(article)

    print("get_rss_links completed")
    return {"articles": rss_data, "messages": [AIMessage(content="Completed getting RSS links")]}

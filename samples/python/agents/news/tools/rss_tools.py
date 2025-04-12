import xml.etree.ElementTree as ET
import requests
import json

from state import GraphState, Article

def get_rss_feed(state: GraphState):
    url = state['data']
    response = requests.get(url)

    return {"data": response.text}

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

    return {"articles": rss_data}

from bs4 import BeautifulSoup

def extract_text_from_html_document(html: str):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text()
    return text

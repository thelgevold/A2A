from langchain_ollama import ChatOllama
from langchain_core.tools import tool
import httpx

model_llm_tools = None

@tool
def get_exchange_rate(
    currency_from: str = "USD",
    currency_to: str = "EUR",
    currency_date: str = "latest",
):
    """Use this to get current exchange rate.

    Args:
        currency_from: The currency to convert from (e.g., "USD").
        currency_to: The currency to convert to (e.g., "EUR").
        currency_date: The date for the exchange rate or "latest". Defaults to "latest".

    Returns:
        A dictionary containing the exchange rate data, or an error message if the request fails.
    """    
    try:
        response = httpx.get(
            f"https://api.frankfurter.app/{currency_date}",
            params={"from": currency_from, "to": currency_to},
        )
        response.raise_for_status()

        data = response.json()

        print(data)

        if "rates" not in data:
            return {"error": "Invalid API response format."}
        return data
    except httpx.HTTPError as e:
        return {"error": f"API request failed: {e}"}
    except ValueError:
        return {"error": "Invalid JSON response from API."} 

def init_llm(): 
    global model_llm_tools

    if model_llm_tools == None:
        model_llm_tools = ChatOllama(model="cogito", base_url = "http://localhost:11435")
        model_llm_tools = model_llm_tools.bind_tools([get_exchange_rate])

    return model_llm_tools

from datetime import datetime
from .base_tool import BaseTool
from utils.utils import timeit_decorator, BING_SEARCH_KEY
import random
import requests
import chainlit as cl

class GetCurrentTimeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="Returns the current time.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @timeit_decorator
    async def handle(self, **kwargs) -> dict:
        return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

class GetRandomNumberTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_random_number",
            description="Returns a random number between 1 and 100.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @timeit_decorator
    async def handle(self, **kwargs) -> dict:
        return {"random_number": random.randint(1, 100)}

class BingSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="bing_search",
            description="Search the internet using Bing search engine.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Prompt describing what to search for on the internet.",
                    },
                    "count": {
                        "type": "integer",
                        "description": "The nummber of search results to retrieve.",
                    },
                },
                "required": ["prompt"],
            },
        )
        
    @timeit_decorator
    async def handle(
        self, prompt: str, api_key: str = BING_SEARCH_KEY, count: int = 10
    ) -> dict:
        """
        Perform a Bing web search.

        Args:
            prompt (str): The search query.
            api_key (str): Your Bing Search API key.
            count (int): Number of search results to retrieve (default is 10).
        
        Returns:
            list: A list of search results, each containing title, snippet, and URL.
        """
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        print(count)
        params = {"q": prompt, "count": count, "textDecorations": True, "textFormat": "HTML"}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            search_results = response.json()

            results = []
            if "webPages" in search_results:
                for item in search_results["webPages"]["value"]:
                    results.append({
                        "title": item.get("name"),
                        "snippet": item.get("snippet"),
                        "url": item.get("url")
                    })
            #print(results)
            return {"status": "search suceeded", "results": results}
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {"status": "search failed"}

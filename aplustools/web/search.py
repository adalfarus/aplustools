from aplustools.web.utils import get_user_agent
import random
import requests
from typing import List, Union, Optional, Generator, Dict
from bs4 import BeautifulSoup
import time


class Search:
    def __init__(self, core=None, local_user_agent_num: int = 5):
        self.core = core
        self.local_user_agent_list = [get_user_agent() for _ in range(local_user_agent_num)]

    def get_useragent(self) -> str:
        return random.choice(self.local_user_agent_list)

    def replace_core(self, new_core):
        self.core = new_core

    def search(self, prompt: str, num_results: int = 10):
        if self.core:
            return self.core.search(query=prompt, num_results=num_results, user_agent=self.get_useragent())
        return prompt

    def api_search(self, prompt: str, api_key: str, num_results: int = 10):
        if self.core:
            return self.core.api_search(query=prompt, api_key=api_key, num_results=num_results)
        return prompt


class BingSearchCore:
    def search(self, prompt, user_agent):
        return prompt

    def api_search(self, query, api_key, custom_config_id: str = "", num_results=10):
        search_url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "customconfig": custom_config_id,
            "count": num_results
        }
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


class GoogleSearchCore:
    def search(self, query: str, num_results: int = 10, user_agent: str = "", advanced: bool = False, check: bool = True,
               blacklisted_websites: Optional[List[str]] = None) -> Union[List[str], List[Dict[str, str]]]:
        proxies = None  # If you have proxy settings, configure them here
        escaped_term = query.replace(" ", "+")
        start = 0
        results = []

        while start < num_results:
            resp = requests.get(
                url="https://www.google.com/search",
                headers={"User-Agent": user_agent},
                params={
                    "q": escaped_term,
                    "num": num_results + 2,
                    "start": start,
                },
                proxies=proxies,
                timeout=5,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            result_block = soup.find_all("div", attrs={"class": "g"})

            for result in result_block:
                link = result.find("a", href=True)
                title = result.find("h3")
                description_box = result.find("div", {"style": "-webkit-line-clamp:2"})

                if description_box:
                    description = description_box.text

                    if link and title and description:
                        url = link["href"]
                        if check and blacklisted_websites and any(
                                blacklisted_website in url for blacklisted_website in blacklisted_websites):
                            continue
                        start += 1
                        if advanced:
                            results.append({"url": url, "title": title.text, "description": description})
                        else:
                            results.append(url)
                        if len(results) == num_results:
                            break

            time.sleep(1)  # Sleep interval to prevent rapid requests

        return results

    def api_search(query, api_key, cse_id, num_results=10, start=1):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": num_results,
            "start": start
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.json()


class DuckDuckGoSearchCore:
    pass


def local_test():
    searcher = Search()  # BingSearchCore())
    # searcher.search("Hello World")
    searcher.replace_core(GoogleSearchCore())
    searcher.search("Hello World")


if __name__ == "__main__":
    local_test()

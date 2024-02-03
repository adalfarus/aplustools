from urllib.parse import urlencode, urlunparse, quote_plus, urlparse, urljoin
import requests
from duckduckgo_search import DDGS
import random
from bs4 import BeautifulSoup
import re
import json
from html import unescape
from typing import Type, Union, Optional, TypeVar, Generic, List
import time


T = TypeVar('T', bound='NonIterable')

class NonIterable(Generic[T]):
    def __init__(self, value: T) -> None:
        if hasattr(value, '__iter__'):
            raise ValueError(f'Value {value} is iterable, which is not allowed.')
        self.value = value

def get_useragent() -> str:
    _useragent_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0',
        "Mozilla/5.0 (Windows NT 8.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    ]
    return random.choice(_useragent_list)

def check_url(url: str, urlTitle: str, inTitle: Optional[Union[str, List[str]]]=None, blacklisted_websites: Optional[list]=None) -> Optional[str]:
    if inTitle is not None and not isinstance(inTitle, list): inTitle = [inTitle]
    if inTitle is None or all([str(x).lower() in urlTitle.lower() for x in inTitle]):
        # Checking if the URL is accessible or leads to a 404 error
        try:
            response = requests.head(url, allow_redirects=True)  # Using HEAD request to get the headers
            if response.status_code == 404:
                print(f"The URL {url} leads to a 404 error, checking next result...")
                return None
        except requests.RequestException as e:
            print(f"Error accessing URL {url}: {e}, checking next result...")
            return None
        if is_crawlable(url):
            if blacklisted_websites is None or not url.split("/")[2] in blacklisted_websites:
                return url
            else:
                print("Blacklisted URL:", url)
        else:
            print(f"The URL {url} cannot be crawled, checking next result...")
    return None
    
def is_crawlable(url: str) -> bool:
    """
    Check if the URL can be crawled by checking the robots.txt file of the website.
    """
    try:
        # Parse the given URL to get the netloc (domain) part
        domain = urlparse(url).netloc
        # Create the URL of the website's robots.txt file
        robots_txt_url = urljoin(f'https://{domain}', 'robots.txt')
        # Send a GET request to the robots.txt URL
        response = requests.get(robots_txt_url)
        # If the request was successful, check if the User-agent is allowed to crawl the URL
        if response.status_code == 200:
            # If "Disallow: /" is found for User-agent: *, it means the website can't be crawled
            if 'User-agent: *\nDisallow: /' in response.text:
                return False
            return True
        else:
            print(f"Failed to retrieve the robots.txt file, status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while checking the robots.txt file: {e}")
    return False  # Return False if there was an error or the robots.txt file couldn't be retrieved

class Search:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        
    def google_provider(self, queries: Union[str, List[str]], blacklisted_websites: Optional[list]=None) -> Optional[str]:
        user_agent = get_useragent()

        def search(query, num_results=10, lang="en", proxy=None, advanced=False, sleep_interval=0, timeout=5):
            proxies = {"https": proxy} if proxy and proxy.startswith("https") else {"http": proxy} if proxy else None
            escaped_term = query.replace(" ", "+")
            start = 0

            while start < num_results:
                resp = requests.get(
                    url="https://www.google.com/search",
                    headers={"User-Agent": user_agent},
                    params={
                        "q": escaped_term,
                        "num": num_results + 2,
                        "hl": lang,
                        "start": start,
                    },
                    proxies=proxies,
                    timeout=timeout,
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
                            start += 1
                            if advanced:
                                yield {"url": link["href"], "title": title.text, "description": description}
                            else:
                                yield link["href"]

                time.sleep(sleep_interval)

        if queries is not None and not isinstance(queries, list): queries = [queries]
        for query in queries:
            results = search(query, num_results=10, advanced=True)
            for i in results:
                url = check_url(i['url'], i['title'], blacklisted_websites=blacklisted_websites)
                if url:
                    print("Found URL:", url)
                    return url
        
        print("No crawlable URL found.")
        return None
        
    def _duckduckgo_provider(self, queries: Union[str, List[str]], blacklisted_websites: Optional[list]=None) -> Optional[Union[bool, str]]:
        def ddg_instant_answer_search(query):
            params = {
                "q": query,
                "format": "json"
            }

            url = "https://api.duckduckgo.com/"
            resp = requests.get(url, params=params, headers=self.headers)
            if resp.status_code != 200:
                print("Failed to retrieve the search results.")
                return False
            
            try:
                data = resp.json()
                results = data.get("Results", [])
                if results:
                    for result in results:
                        yield {
                            "title": unescape(result["Text"]),
                            "url": result["FirstURL"],
                            "body": unescape(data["AbstractText"])
                        }
            except ValueError:
                print("Failed to parse the search results.")
                return False

        if queries is not None and not isinstance(queries, list): queries = [queries]
        for query in queries: # Added, so you can pass a single string
            results = ddg_instant_answer_search(query)
            for r in results:
                print(r)
                url = check_url(r['url'], r['title'], blacklisted_websites=blacklisted_websites)
                if url:
                    print("Found URL:", url)
                    return url

        print("No crawlable URL found.")
        return None
        
    def duckduckgo_provider(self, queries: Union[str, List[str]], blacklisted_websites: Optional[list]=None) -> Optional[str]:
        import warnings
        warnings.warn(
            "This function doesn't work at the momen. Please use google_provider instead till it's fixed.",
            UserWarning,
            stacklevel=2)
        with DDGS(timeout=20) as ddgs:
            for query in list(queries): # Added, so you can pass a single string
                results = ddgs.text(query, timelimit=100, safesearch='off')
                for r in results:
                    url = check_url(r['href'], r['title'], blacklisted_websites=blacklisted_websites)
                    if url:
                        print("Found URL:", url)
                        return url
        print("No crawlable URL found.")
        return None
        
    def bing_provider(self, queries: Union[str, List[str]], blacklisted_websites: Optional[list]=None) -> Optional[str]:
        user_agent = get_useragent()
        
        def bing_search(query, num_results=10):
            url = f'https://www.bing.com/search?q={quote_plus(query)}'
            headers = {"User-Agent": user_agent}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print("Failed to retrieve the search results.")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            links = [
                (a.text, a['href']) for a in soup.find_all('a', href=True) if 'http' in a['href']
            ]

            for link in links[:num_results]:  # limiting the number of results
                yield {"title": link[0], "url": link[1]}

        if queries is not None and not isinstance(queries, list): queries = [queries]
        for query in list(queries): # Added, so you can pass a single string
            results = bing_search(query, num_results=10)
            for i in results:
                url = check_url(i['url'], i['title'], blacklisted_websites=blacklisted_websites)
                if url:
                    print("Found URL:", url)
                    return url
        
        print("No crawlable URL found.")
        return None
    
def local_test():
    try:
        search = Search()
        result = search.google_provider("Cats")
        print(result)
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True

if __name__ == "__main__":
    local_test()

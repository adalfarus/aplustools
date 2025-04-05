"""TBA"""
from urllib.parse import quote_plus as _quote_plus, urlparse as _urlparse, urljoin as _urljoin
import random as _random

from ..package import enforce_hard_deps as _enforce_hard_deps
from ..io.env import auto_repr as _auto_repr

import requests as _requests
import bs4 as _bs4

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = ["requests", "bs4"]
_enforce_hard_deps(__hard_deps__, __name__)


def url_validator(url: str) -> bool:
    """TBA"""
    try:
        result = _urlparse(url)
        return all((result.scheme, result.netloc))
    except AttributeError:
        return False


@_auto_repr
class WebPage:
    """TBA"""
    def __init__(self, url: str) -> None:
        self._url: str = url
        self._user_agent: str = self.generate_user_agent()
        self._headers: dict[str, str] = {"User-Agent": self._user_agent}

        self._crawlable: bool = self.is_crawlable(self._url)
        self._accessible: bool
        self._status_code: int
        self._accessible, self._status_code = self.check_url(self._url)

        self._page: _requests.Response | None = None
        self._soup: _bs4.BeautifulSoup | None = None

        if self._accessible and self._crawlable:
            self.fetch_page()

    @staticmethod
    def is_crawlable(url: str, timeout: float = 2.0) -> bool | None:
        """TBA, if unclear returns None"""
        try:  # Parse the given URL to get the netloc (domain) part
            domain: str = _urlparse(url).netloc
            robots_txt_url: str = _urljoin(f"https://{domain}", "robots.txt")
            response: _requests.Response = _requests.get(robots_txt_url, timeout=timeout)

            if response.status_code == 200:  # We check, if "Disallow: /" is found for User-agent: *, if ...
                cases: tuple[bool, ...] = ("User-agent: *\nDisallow: /" in response.text, True)
                return not any(cases)
            return None
        except _requests.RequestException:
            return None

    @staticmethod
    def check_url(url: str, timeout: float = 2.0) -> int | None:
        """TBA, returns status code, None if unclear"""
        try:
            response: _requests.Response = _requests.head(url, allow_redirects=True, timeout=timeout)
            status_code: int | None = response.status_code
        except _requests.RequestException:
            status_code: int | None = None
        return status_code

    @staticmethod
    def generate_user_agent() -> str:
        """TBA"""
        platforms: tuple[str, ...] = (
            f"Windows NT {_random.choice([10, 11])}.0; Win64; x64",
            f"Macintosh; Intel Mac OS X 10_15_7",
            f"X11; Linux x86_64",
            f"iPhone; CPU iPhone OS {_random.choice(range(10, 13))}_{_random.choice(range(0, 7))} like Mac OS X",
            f"Android {_random.choice(range(8, 12))}; Mobile"
        )
        browsers: tuple[str, ...] = (
            "Mozilla/5.0 ({platform}) Gecko/20100101 Firefox/{firefox_version}",
            "Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
            "Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36 Edg/{edge_version}",
            "Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15",
            "Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Opera/{opera_version} Safari/537.36"
        )

        platform: str = _random.choice(platforms)
        browser_template: str = _random.choice(browsers)
        firefox_version: str = f"{_random.randint(50, 90)}.0"
        chrome_version: str = f"{_random.randint(70, 110)}.0.0.0"
        edge_version: str = f"{_random.randint(70, 100)}.0.{_random.randrange(1000, 2000)}.{_random.randrange(50, 99)}"
        opera_version: str = f"{_random.randint(60, 75)}.0.0.0"

        user_agent: str = browser_template.format(platform=platform, firefox_version=firefox_version,
                                             chrome_version=chrome_version, edge_version=edge_version,
                                             opera_version=opera_version)
        return user_agent

    def fetch_page(self, timeout: float = 2.0) -> None:
        """TBA"""
        try:
            self._page = _requests.get(self._url, headers=self._headers, timeout=timeout)
            self._soup = _bs4.BeautifulSoup(self._page.content, "html.parser")
        except _requests.RequestException:
            return

    def get_by_tag(self, tag: str) -> list[_bs4.element.Tag] | None:
        """TBA"""
        if self._soup is None:
            return None
        return self._soup.find_all(tag)

    def get_by_class(self, class_name: str) -> list[_bs4.element.Tag] | None:
        """TBA"""
        if self._soup is None:
            return None
        return self._soup.find_all(class_=class_name)

    def from_soup(self, func_name: str, *args: _ty.Any, **kwargs: _ty.Any) -> _ty.Any | None:
        """TBA"""
        if self._soup is None or not hasattr(self._soup, func_name):
            return None
        method = getattr(self._soup, func_name)
        if not callable(method):
            return None
        try:
            return method(*args, **kwargs)
        except Exception as e:
            raise RuntimeError("Called soup function has thrown an error") from e

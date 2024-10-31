"""TBA"""

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__ = []
__hard_deps__ = ["bs4"]
_enforce_hard_deps(__hard_deps__, __name__)


class Search:
    ...


class SearchCore:  # Interface
    ...


class BingSearchCore(SearchCore):
    ...


class GoogleSearchCore(SearchCore):
    ...


class DuckDuckGoSearchCore(SearchCore):
    ...


# Add other search engines

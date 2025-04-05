"""TBA"""
from ssl import create_default_context as _create_default_context
from http.client import HTTPSConnection as _HTTPSConnection
import concurrent.futures as _concurrent_futures
from urllib.parse import urlparse as _urlparse
import requests as _requests
import asyncio as _asyncio
import certifi as _certifi

from ..io.concurrency import LazyDynamicThreadPoolExecutor as _LazyDynamicThreadPoolExecutor
from ..package import enforce_hard_deps as _enforce_hard_deps
from ..package import optional_import as _optional_import

_aiohttp = _optional_import("aiohttp")

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = ["aiohttp>=3.9.5"]
__hard_deps__: list[str] = ["certifi"]
_enforce_hard_deps(__hard_deps__, __name__)


def _get_data_manual(url: str, method: str = "GET", data: _ty.Any = None) -> bytes:
    """
    Internal method to fetch the data from a URL using HTTPSConnection and SSL context.
    """
    context = _create_default_context(cafile=_certifi.where())
    parsed_url = _urlparse(url)

    if parsed_url.hostname is None:
        raise ValueError(f"The URL '{url}' lacks a scheme")

    conn = _HTTPSConnection(parsed_url.hostname, context=context)
    uri = parsed_url.path + ('?' + parsed_url.query if parsed_url.query else '')

    conn.request(method, uri, body=data)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    return data


def _get_data(url: str, method: str = "GET", data: _ty.Any = None) -> bytes:
    """
    Fetches data from the specified URL using the `requests` library.

    Args:
        url (str): The URL to fetch the data from.
        method (str): The HTTP method to use (GET, POST, etc.). Defaults to "GET".
        data (_ty.Any, optional): Optional data to send with the request. Defaults to None.

    Returns:
        bytes: The response content as raw bytes.
    """
    try:
        # Handle GET and POST requests; add other methods if needed.
        if method == "GET":
            response = _requests.get(url)
        elif method == "POST":
            response = _requests.post(url, data=data)
        else:
            raise ValueError(f"HTTP method '{method}' is not supported.")

        # Raise an error for HTTP error codes (e.g., 404, 500)
        response.raise_for_status()

        return response.content  # Return the raw bytes from the response

    except _requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching {url}: {e}")
        return b""  # Return empty bytes in case of an error


def fetch(url: str) -> bytes:
    """
    Fetch a web resource from the specified URL using HTTPSConnection and SSL context.

    Args:
        url (str): The URL of the web resource to fetch.

    Returns:
        bytes: The fetched resource as raw bytes.
    """
    return _get_data(url, "GET")


class Result:
    """
    A class to handle a list of futures, allowing the user to process results
    once the futures are completed. It supports transformations on results and
    different modes for collecting them.

    Attributes:
        futures (list[_concurrent_futures.Future]): A list of future objects representing asynchronous tasks.
        no_into_results (list[_ty.Any]): A list initialized to store raw results, which can later be populated.
        _into_done (bool): A flag to indicate whether an 'into' method has been used.
    """
    def __init__(self, futures: list[_concurrent_futures.Future]):
        """
        Initializes the Result class with a list of future objects.

        :param futures: A list of futures representing asynchronous operations.
        """
        self.futures: list[_concurrent_futures.Future] = futures
        self.no_into_results: list[_ty.Any] = [None] * len(futures)
        self._into_done: bool = False

    def _make_fut_callback(self, _process_result, idx) -> _a.Callable:
        """
        Creates a callback for when a future is completed.

        :param _process_result: The function that will process the result of the future.
        :param idx: The index of the future in the list.
        :return: A callable to be used as a callback.
        """
        return lambda fut: _process_result(fut, idx)

    def into(self, container: list[_a.Callable[[_ty.Any], None] | _ty.Type]) -> _ty.Self:
        """
        Process each result as it finishes and apply the transformation specified by
        the container's elements (e.g., `str`, `json.loads`, etc.) to the result.

        :param container: A list of callable transformations (e.g., str, json.loads) or types.
        :return: Self, to allow for chaining.
        :raises ValueError: If the length of the container doesn't match the number of futures
                            or if another 'into' method has already been called.
        """
        if len(container) != len(self.futures):
            raise ValueError(f"Container should be of length '{len(self.futures)}' "
                             f"but is of length '{len(container)}'")
        elif self._into_done:
            raise ValueError("You cannot use .into([..]) if you've already used another into_... method.")
        self._into_done = True

        # Append the futures to the container as soon as they are completed.
        def _process_result(future, index):
            result = future.result()  # This blocks until the future is done
            container[index] = container[index](result)  # Store the result into the container

        # Attach the processor to each future
        for idx, future in enumerate(self.futures):
            # Add a done callback that will store the result in the container
            future.add_done_callback(self._make_fut_callback(_process_result, idx))

        return self  # Return self so you can chain await()

    def no_into(self) -> _ty.Self:
        """
        Collects raw results and stores them in the `null_results` list without any transformation.

        :return: Self, to allow for chaining.
        :raises ValueError: If another 'into' method has already been called.
        """
        if self._into_done:
            raise ValueError("You cannot use .into_null() if you've already used another into_... method.")
        self._into_done = True

        # Append the futures to the container as soon as they are completed.
        def _process_result(future, index):
            self.no_into_results[index] = future.result()

        # Attach the processor to each future
        for idx, future in enumerate(self.futures):
            # Add a done callback that will store the result in the container
            future.add_done_callback(self._make_fut_callback(_process_result, idx))

        return self

    def await_(self) -> _ty.Self:
        """
        Waits for all futures to finish by blocking until they are done.

        :return: Self, after all futures have completed.
        """
        for future in self.futures:
            future.result()  # Ensure all futures are done and processed
        return self


class UnifiedRequestHandler:
    """
    A request handler that submits HTTP requests using a dynamic thread pool executor.
    It supports both synchronous and asynchronous modes for handling single or multiple
    requests at once.

    Configurations known to work well are:

    - (2, 10, 5), 5.0 (Diamond, testing 0.47->0.81 seconds for 10 web requests; 0.9->1.3 seconds for 20 web requests)

    - ({min_workers e.g. 5}, {big n like 100}, 10), 2.0 (Gold, testing 0.7->1.2 seconds for 200 web requests)

    - ({min_workers e.g. 5}, {big n like 100}, 5), 1.0 (Silver, testing 0.8->1.6 seconds for 200 web requests)


    Attributes:
        _pool (_LazyDynamicThreadPoolExecutor): A dynamically sized thread pool for executing tasks.
    """

    def __init__(self, min_workers: int = 2, max_workers: int = 10, workers_step: int = 5,
                 check_interval: float = 5.0) -> None:
        """
        Initializes the request handler with a dynamic thread pool.

        :param min_workers: The minimum number of worker threads to maintain in the pool.
        :param max_workers: The maximum number of worker threads allowed in the pool.
        :param workers_step: The increment or decrement in the number of workers during pool resizing.
        :param check_interval: The time interval, in seconds, to wait before checking if the pool
                               needs resizing based on current load.
        """
        self._pool = _LazyDynamicThreadPoolExecutor(min_workers, max_workers, check_interval, workers_step)

    @property
    def current_size(self) -> int:
        """
        Returns the current size of the dynamic thread pool.

        :return: Number of currently active threads in the pool.
        """
        return len(self._pool._threads)

    @property
    def pool(self) -> _LazyDynamicThreadPoolExecutor:
        """
        Returns the internal pool instance. This is done, so you don't need a pool exclusively for web requests.
        :return: _LazyDynamicThreadPoolExecutor
        """
        return self._pool

    def request(self, url: str, async_mode: bool = False, method: str = "GET", data: _ty.Any = None
                ) -> _concurrent_futures.Future | bytes:
        """
        Submits an HTTP request. Supports both synchronous and asynchronous execution.

        :param url: The URL to make the request to.
        :param async_mode: Whether to run the request in asynchronous mode (returns a future).
        :param method: The HTTP method to use (default is "GET").
        :param data: Any additional data to be passed with the request.
        :return: A future if in async mode, or the result bytes in synchronous mode.
        """
        if async_mode:
            # Submit the request to the thread pool and return the future
            future = self._pool.submit(_get_data, url, method, data)
            return future  # Return future object for async mode
        else:
            # Synchronous mode, just return the result
            return _get_data(url, method, data)

    def request_many(self, urls: list[str], async_mode: bool = False, method: str = "GET", data: _ty.Any = None
                     ) -> Result | list[bytes]:
        """
        Submits multiple requests concurrently. Supports both synchronous and asynchronous execution.

        :param urls: A list of URLs to make requests to.
        :param async_mode: Whether to run the requests in asynchronous mode (returns a Result object).
        :param method: The HTTP method to use for all requests (default is "GET").
        :param data: Any additional data to be passed with the request.
        :return: A Result object in async mode or a list of bytes in synchronous mode.
        """
        if async_mode:
            futures = [self._pool.submit(_get_data, url, method, data) for url in urls]
            return Result(futures)  # Return the result object
        else:
            result = []
            for url in urls:
                result.append(_get_data(url, method, data))
            return result

    def shutdown(self) -> None:
        """
        Shuts down the thread pool gracefully, waiting for all threads to finish their tasks.
        """
        self._pool.shutdown(wait=True)

    def __del__(self) -> None:
        self.shutdown()


class UnifiedRequestHandlerAdvanced:
    """
    Unified request handler that uses aiohttp for asynchronous HTTP requests and integrates
    with AsyncIOResult to handle multiple async requests concurrently. Public-facing methods
    are synchronous, while the internal logic is fully async.
    """

    def __init__(self) -> None:
        if _aiohttp is None:
            raise RuntimeError("AIOHttp is not installed")
        self.session: _aiohttp.ClientSession | None = None
        self.loop: _asyncio.AbstractEventLoop | None = None

    async def _initialize_session(self) -> None:
        if not self.session:
            self.session = _aiohttp.ClientSession()

    async def _get_data(self, url: str, method: str = "GET", data: _ty.Any = None) -> bytes:
        async with self.session.request(method, url, data=data) as response:
            return await response.read()

    async def _request_async(self, url: str, method: str = "GET", data: _ty.Any = None) -> bytes:
        await self._initialize_session()
        return await self._get_data(url, method, data)

    async def _request_many_async(self, urls: list[str], method: str = "GET", data: _ty.Any = None) -> _asyncio.gather:
        await self._initialize_session()
        tasks = [_asyncio.create_task(self._get_data(url, method, data)) for url in urls]
        return await _asyncio.gather(*tasks)

    def _get_or_create_event_loop(self) -> _asyncio.AbstractEventLoop:
        """
        Get the running event loop or create a new one if none exists.
        """
        try:
            # Try to get the running event loop
            loop = _asyncio.get_running_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
            return loop
        except RuntimeError:
            # No running event loop, create a new one
            if self.loop is None:
                self.loop = _asyncio.new_event_loop()
            return self.loop

    def _run_in_event_loop(self, coro: _ty.Any) -> _ty.Any:
        """
        Run a coroutine in the event loop. Create a new loop if needed.
        """
        loop = self._get_or_create_event_loop()
        return loop.run_until_complete(coro)

    def request(self, url: str, method: str = "GET", data: _ty.Any = None) -> bytes:
        """
        Public-facing synchronous method to submit a request. Internally runs the async code.
        """
        return self._run_in_event_loop(self._request_async(url, method, data))

    def request_many(self, urls: list[str], method: str = "GET", data: _ty.Any = None) -> list[bytes]:
        """
        Public-facing synchronous method to submit multiple requests. Internally runs the async code.
        """
        return self._run_in_event_loop(self._request_many_async(urls, method, data))

    def shutdown(self) -> None:
        """
        Shutdown the request handler and close the session if it exists.
        """
        if self.session:
            self._run_in_event_loop(self.session.close())
            self.session = None
        if self.loop:
            self.loop.close()
            self.loop = None

    def __del__(self) -> None:
        self.shutdown()

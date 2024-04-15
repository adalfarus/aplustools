# -----------------------------------
# This is an internal module used to
# handle stacked requests and async
# requests automatically without
# needing extra code.
# -----------------------------------
import requests
import asyncio
import aiohttp
import os


async def _async_fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


def _sync_fetch(url):
    response = requests.get(url)
    return response.text


def fetch(url, async_mode=False):
    if async_mode:
        return asyncio.run(_async_fetch(url))
    else:
        return _sync_fetch(url)


class UnifiedRequestHandler:
    _global_session = None  # Only for async requests

    def __init__(self, use_global_session: bool = False):
        self.use_global_session = use_global_session
        self._session = self._global_session if use_global_session else None

    async def _async_fetch(self, url):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        async with self._session.get(url) as response:
            return await response.text()

    @staticmethod
    def _sync_fetch( url):
        response = requests.get(url)
        return response.text

    async def fetch(self, url, async_mode=False):
        if async_mode:
            return await self._async_fetch(url)
        else:
            return self._sync_fetch(url)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class UnifiedRequestHandlerAdvanced:
    def __init__(self):
        self.session = None  # Only for async requests

    async def _async_request(self, method, url, return_type='text', **kwargs):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        async with self.session.request(method, url, **kwargs) as response:
            response.raise_for_status()
            if return_type == 'binary':
                return await response.read()
            return await response.text()

    @staticmethod
    def _sync_request(method, url, return_type='text', **kwargs):
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        if return_type == 'binary':
            return response.content
        return response.text

    async def request(self, method, url, async_mode=False, return_type='text', **kwargs):
        if async_mode:
            return await self._async_request(method, url, return_type, **kwargs)
        else:
            return self._sync_request(method, url, return_type, **kwargs)


def local_test():
    try:
        # Default request handler
        handler = UnifiedRequestHandler()

        # Synchronous request
        handler.fetch('http://example.com', async_mode=False)
        # Asynchronous request
        handler.fetch('http://example.com', async_mode=True)

        # Advanced request handler (you can pass extra keyword arguments, and it automatically raises for status)
        adv_handler = UnifiedRequestHandlerAdvanced()  # It can also handle image content

        # Synchronous GET request
        adv_handler.request('GET', 'http://example.com', async_mode=False)
        # Asynchronous GET request
        adv_handler.request('GET', 'http://example.com', async_mode=True)

        folder_path = "./test_data/images"
        os.makedirs(folder_path, exist_ok=True)

        # Synchronous binary request (e.g., image)
        image_content = adv_handler.request('GET', 'https://huggingface.co/p1atdev/MangaLineExtraction-hf/resolve/main/images/sample.jpg', async_mode=False, return_type='binary')
        with open(os.path.join(folder_path, './image.jpg'), 'wb') as file:
            file.write(image_content)

        # Asynchronous binary request (e.g., image)
        image_content_async = adv_handler.request('GET', 'https://huggingface.co/p1atdev/MangaLineExtraction-hf/resolve/main/images/sample.jpg', async_mode=True, return_type='binary')
        with open(os.path.join(folder_path, './image_async.jpg'), 'wb') as file:
            file.write(image_content_async)
    except Exception as e:
        print(f"An error occurred {e}")
        return False
    print("All tests succeeded successfully")
    return True


if __name__ == "__main__":
    local_test()

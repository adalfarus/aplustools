import requests
import asyncio
import aiohttp
import os


async def _async_fetch(url, session):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def _sync_fetch(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def fetch(url, async_mode=False):
    if async_mode:
        async def wrapper():
            async with aiohttp.ClientSession() as session:
                return await _async_fetch(url, session)
        return asyncio.run(wrapper())
    else:
        return _sync_fetch(url)


class UnifiedRequestHandler:
    @staticmethod
    async def _async_fetch(url):
        async with aiohttp.ClientSession() as session:
            return await _async_fetch(url, session)

    @staticmethod
    def _sync_fetch(url):
        return _sync_fetch(url)

    @classmethod
    def fetch(cls, url, async_mode=False):
        if async_mode:
            return asyncio.run(cls._async_fetch(url))
        else:
            return cls._sync_fetch(url)


class UnifiedRequestHandlerAdvanced:
    @staticmethod
    async def _async_request(method, url, return_type='text', **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
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

    @classmethod
    def request(cls, method, url, async_mode=False, return_type='text', **kwargs):
        if async_mode:
            return asyncio.run(cls._async_request(method, url, return_type, **kwargs))
        else:
            return cls._sync_request(method, url, return_type, **kwargs)


# AIO Files


def local_test():
    try:
        from src.aplustools import TimidTimer
        timer = TimidTimer()

        # Synchronous request
        UnifiedRequestHandler.fetch('http://example.com', async_mode=False)

        for _ in range(20):
            # Asynchronous request
            UnifiedRequestHandler.fetch('http://example.com', async_mode=True)

        print("Average time for 20 rounds async (fetch):", timer.end() / 20)

        timer.start()

        # Synchronous GET request
        UnifiedRequestHandlerAdvanced.request('GET', 'http://example.com', async_mode=False)

        for _ in range(20):
            # Asynchronous GET request
            UnifiedRequestHandlerAdvanced.request('GET', 'http://example.com', async_mode=True)

        print("Average time for 20 rounds async (request):", timer.end() / 20)

        print("Normal requests done, getting images now ...")

        folder_path = "./test_data/images"
        os.makedirs(folder_path, exist_ok=True)

        # Synchronous binary request (e.g., image)
        image_content = UnifiedRequestHandlerAdvanced.request('GET', 'https://huggingface.co/p1atdev/MangaLineExtraction-hf/resolve/main/images/sample.jpg', async_mode=False, return_type='binary')
        print("Got image")
        with open(os.path.join(folder_path, './image.jpg'), 'wb') as file:
            file.write(image_content)

        # Asynchronous binary request (e.g., image)
        image_content_async = UnifiedRequestHandlerAdvanced.request('GET', 'https://huggingface.co/p1atdev/MangaLineExtraction-hf/resolve/main/images/sample.jpg', async_mode=True, return_type='binary')
        print("Got image async")
        with open(os.path.join(folder_path, './image_async.jpg'), 'wb') as file:
            file.write(image_content_async)
    except Exception as e:
        print(f"Exception occurred: {e}")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    local_test()

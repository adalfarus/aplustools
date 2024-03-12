# from imagetools import *
import cv2
import numpy as np
import base64
from io import BytesIO
from typing import Optional, Tuple, Union
import asyncio
from aiohttp import ClientSession
from typing import Type, Union, Tuple, Optional, List
from concurrent.futures import ThreadPoolExecutor
import functools
import mimetypes
import requests
import os
from urllib.parse import urlparse, urljoin


class ImageManager:
    def __init__(self, base_location: Optional[str] = None, use_async: bool = False):
        self.base_location = base_location
        self.images: List[Union[OfflineImage, OnlineImage]] = []
        self.use_async = use_async

    def add_image(self, image_class: Type[Union['OfflineImage', 'OnlineImage']], *args, **kwargs) -> int:
        """
        Creates and adds an image objects.

        Parameters:
            image_class -- The image class for the object
            args -- The positional arguments for the image_class
            kwargs -- The keyword arguments for the image_class
        """

        kwargs["base_location"] = kwargs.get("base_location") or self.base_location
        if self.use_async:
            kwargs["_use_async"] = True
            asyncio.run(self._add_image_async(image_class, *args, **kwargs))
        else:
            kwargs["_use_async"] = False
            self.images.append(image_class(*args, **kwargs))
        return len(self.images) - 1

    async def _add_image_async(self, image_class: Type[Union['OfflineImage', 'OnlineImage']], *args, **kwargs):
        self.images.append(await self.create_async(image_class, *args, **kwargs))

    @staticmethod
    async def create_async(cls, *args, **kwargs):
        # Asynchronously perform initialization tasks here
        instance = cls(*args, **kwargs)
        # Optionally perform more async operations on 'instance' if needed
        return instance

    def add_images(self, images_info: List[Tuple[Type[Union['OfflineImage', 'OnlineImage']], tuple, dict]]):
        """
        Creates and adds multiple image objects.

        Parameters:
            images_info -- First is the image class for the object, then an argument tuple and at last a keyword
            argument dictionary
        """
        if self.use_async:
            asyncio.run(self._add_images_async(images_info))
        else:
            for image_class, args, kwargs in images_info:
                kwargs["base_location"] = kwargs.get("base_location") or self.base_location
                kwargs["_use_async"] = False
                self.images.append(image_class(**kwargs))

    async def _add_images_async(self, images_info):
        tasks = [ImageClass(*args, **{**kwargs, "_use_async": True,
                                      "base_location": kwargs.get("base_location") or self.base_location})
                 for ImageClass, args, kwargs in images_info]
        self.images.extend(await asyncio.gather(*tasks))

    def add_image_object(self, image_object: Union['OfflineImage', 'OnlineImage']) -> int:
        """Adds image objects."""
        self.images.append(image_object)
        return len(self.images) - 1

    def add_image_objects(self, image_objects: List[Union['OfflineImage', 'OnlineImage']]):
        """Adds image objects."""
        self.images.extend(image_objects)

    def remove_image(self, index: int):
        if self.use_async:
            asyncio.run(self._remove_image(index))
        else:
            del self.images[index]

    async def _remove_image(self, index: int):
        await asyncio.sleep(0)  # Yield control to the event loop
        del self.images[index]

    def remove_images(self, indices_list: List[int]):
        if self.use_async:
            asyncio.run(self._remove_images(indices_list))
        else:
            for index in sorted(indices_list, reverse=True):
                del self.images[index]

    async def _remove_images(self, indices_list: List[int]):
        tasks = [self._remove_image(index) for index in sorted(indices_list, reverse=True)]
        await asyncio.gather(*tasks)

    def remove_image_object(self, image_object: Union['OfflineImage', 'OnlineImage']):
        if self.use_async:
            asyncio.run(self._remove_image_object(image_object))
        else:
            self.images.remove(image_object)

    async def _remove_image_object(self, image_object: Union['OfflineImage', 'OnlineImage']):
        await asyncio.sleep(0)  # Yield control to the event loop
        self.images.remove(image_object)

    def remove_image_objects(self, image_objects: List[Union['OfflineImage', 'OnlineImage']]):
        if self.use_async:
            asyncio.run(self._remove_image_objects(image_objects))
        else:
            for image_object in image_objects:
                self.images.remove(image_object)

    async def _remove_image_objects(self, image_objects: List[Union['OfflineImage', 'OnlineImage']]):
        tasks = [self._remove_image_object(image_object) for image_object in image_objects]
        await asyncio.gather(*tasks)

    def execute_func(self, index: int, function, *args, **kwargs):
        if self.use_async:
            asyncio.run(self._execute_func_async(index, function, *args, **kwargs))
        else:
            getattr(self.images[index], function)(*args, **kwargs)

    async def _execute_func_async(self, index: int, function, *args, **kwargs):
        func = getattr(self.images[index], function)
        if asyncio.iscoroutinefunction(func):
            await func(*args, **kwargs)
        else:
            # Handle non-async functions, possibly with run_in_executor for CPU-bound methods
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                await self.run_in_executor(loop, pool, func, *args, **kwargs)

    @staticmethod
    async def run_in_executor(loop, executor, func, *args, **kwargs):
        if kwargs:
            func = functools.partial(func, **kwargs)
        return await loop.run_in_executor(executor, func, *args)

    def execute_funcs(self, function_name: str, args_list: List[Tuple[int, list, dict]]):
        if self.use_async:
            asyncio.run(self._execute_funcs_async(function_name, args_list))
        else:
            for index, args, kwargs in args_list:
                try:
                    getattr(self.images[index], function_name)(*args, **kwargs)
                except IndexError:
                    print(f"No image at index {index}")
                except AttributeError:
                    print(f"The function {function_name} does not exist for the image at index {index}")

    async def _execute_funcs_async(self, function_name: str, args_list: List[Tuple[int, list, dict]]):
        tasks = [self._execute_func_async(index, function_name, *args, **kwargs) for index, args, kwargs in args_list]
        await asyncio.gather(*tasks)


class ResizeTypes:
    FAST = cv2.INTER_NEAREST
    LINEAR = cv2.INTER_LINEAR
    AREA = cv2.INTER_AREA
    CUBIC = cv2.INTER_CUBIC
    LANCZOS4 = cv2.INTER_LANCZOS4


class OfflineImage:
    def __init__(self, data: Optional[Union[str, bytes]] = None, path: Optional[str] = None, _use_async: bool = False,
                 base_location: Optional[str] = None):
        if data is not None and path is None:
            self.data = data
        elif path is not None and data is None:
            self.get_data(path)
        else:
            raise ValueError("Please pass exactly one argument ('data' or 'path') to the init method.")
        self._use_async = _use_async
        self.base_location = base_location

    def get_data(self, path: str):
        with open(path, 'rb') as f:
            self.data = f.read()

    def load_image_from_data(self):
        if isinstance(self.data, str):
            # Assuming data is a base64 string
            image_data = base64.b64decode(self.data.split(',')[1])
        elif isinstance(self.data, bytes):
            image_data = self.data
        else:
            raise ValueError("Unsupported data type for self.data")
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_UNCHANGED)
        return image

    def resize_image(self, new_size: Tuple[int, int]) -> None:
        img = self.load_image_from_data()
        resized_image = cv2.resize(img, new_size, interpolation=cv2.INTER_LANCZOS4)

        # Updating self.data with the new image data
        self.update_image_data(resized_image)

    def rotate_image(self, degrees: float) -> None:
        img = self.load_image_from_data()
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, degrees, 1.0)
        rotated_image = cv2.warpAffine(img, M, (w, h))

        # Updating self.data with the new image data
        self.update_image_data(rotated_image)

    def crop_image(self, crop_rectangle: Tuple[int, int, int, int]) -> None:
        img = self.load_image_from_data()
        x, y, w, h = crop_rectangle
        cropped_image = img[y:y+h, x:x+w]

        # Updating self.data with the new image data
        self.update_image_data(cropped_image)

    def update_image_data(self, img):
        _, buffer = cv2.imencode('.png', img)
        self.data = buffer.tobytes()

    def save_image_to_disk(self, file_path: str) -> None:
        if not isinstance(self.data, (bytes, str)):
            raise ValueError("self.data must be a byte string or a base64 string.")
        with open(file_path, "wb") as file:
            file.write(self.data if isinstance(self.data, bytes) else base64.b64decode(self.data.split(',')[1]))

    def convert_to_grayscale(self) -> None:
        img = self.load_image_from_data()
        grayscale_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.update_image_data(grayscale_image)

    def apply_blur(self, ksize: Tuple[int, int] = (5, 5)) -> None:
        img = self.load_image_from_data()
        blurred_image = cv2.GaussianBlur(img, ksize, 0)
        self.update_image_data(blurred_image)

    def resize_image_custom(self, new_size: Tuple[int, int], method=cv2.INTER_LINEAR) -> None:
        img = self.load_image_from_data()
        resized_image = cv2.resize(img, new_size, interpolation=method)
        self.update_image_data(resized_image)


class OnlineImage(OfflineImage):
    def __init__(self, current_url: Optional[str] = None, base_location: str = "../utils\\", one_time: bool = False,
                 _use_async: bool = False):
        self.current_url = current_url
        self.base_location = base_location
        self._use_async = _use_async

        if one_time and current_url:
            self.download_image()

    def download_image(self, img_url: Optional[str] = None, base_path: Optional[str] = None,
                       new_name: Optional[str] = None, img_format: Optional[str] = None
                       ) -> Union[Tuple[bool, None, None], Tuple[bool, str, str]]:
        if not img_url:
            if not self.current_url:
                print("No URL provided for image download.")
                return False, None, None
            img_url = self.current_url
        base_path = base_path or self.base_location

        try:
            response = requests.get(img_url)
            response.raise_for_status()  # Will raise an HTTPError for bad requests (4xx or 5xx)
            image_data = np.frombuffer(response.content, dtype=np.uint8)
            img = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)

            # Determine the file extension if not provided
            if not img_format:
                guessed_extension = mimetypes.guess_extension(response.headers.get('content-type'))
                img_format = guessed_extension.strip('.') if guessed_extension else 'png'  # 'jpg'

            file_name = new_name if new_name else os.path.basename(urlparse(img_url).path).split('.')[0]
            file_path = os.path.join(base_path, f"{file_name}.{img_format}")

            # Save the image data
            cv2.imwrite(file_path, img)
            print(f"Downloaded and saved image from {img_url} to {file_path}")
            super().__init__(path=file_path)
            return True, file_name, file_path

        except requests.ConnectionError:
            print("Failed to connect to the server.")
        except requests.Timeout:
            print("The request timed out.")
        except requests.TooManyRedirects:
            print("Too many redirects.")
        except requests.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except KeyError:
            print("The image tag does not have a src attribute.")
        except Exception as e:
            print(f"An unexpected error occurred while downloading the image: {e}")

        return False, None, None


def local_test():
    try:
        # Setup
        os.makedirs("./test_data/images", exist_ok=True)  # Ensure the test directory exists

        # Initialize OfflineImage with a base64-encoded image
        base64_image_str = ("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBwgHBgkIBwgKCgkLDRYPDQ"
                            "wMDRsUFRAWIB0iIiAdHx8kKDQsJCYxJx8fLT0tMTU3Ojo6Iys/RD84QzQ5OjcBCgoKDQwNGg8PGjclHyU"
                            "3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3N//AABEIAHkAwgMB"
                            "IgACEQEDEQH/xAAcAAABBQEBAQAAAAAAAAAAAAACAAEDBAYFBwj/xABEEAABAwMCAwMGCQkJAQAAAAABA"
                            "AIDBAUREiEGMUETUXEVIjJSYZEUM0KBgpOhsdEHI1NUYmODksEWNENEc5SiwuEX/8QAFwEBAQEBAAAAAA"
                            "AAAAAAAAAAAAECA//EAB0RAQADAQEBAAMAAAAAAAAAAAABAhETEiExUXH/2gAMAwEAAhEDEQA/APRwAjA"
                            "ThoRgLrrjgdKINRhEAmmADEQYjCcKaYEMRgJwnRSCdMnUCSwkllA+E6bKWoIHTpkigSR5JspE7IoXDIQg"
                            "I0yIYoCiKEoGOOqF2EiUJKoWySHKSAQjChDktagsIgVWEiIPQWcp8qFrkQcglyllR6ktSCTKfKj1JakBk"
                            "qN0uE+UD25QCZ0wqFC+N2dkzI3ZVF+KTIyj1BV2jASJOUFgpKFrj1RakB5TIcpi5ARQFIuQkoGJQlJzkD"
                            "nICyko9RSQB0QOymyUwOSiCblSsygapQEC1FOHoT4ISCoqYPT6wq2D3omgjmUE+tPrUWcJa2jmQPE4QS6"
                            "k+pRB7TyIOO4pakEuUtQCi1ISSTzVRYyllV8kJB5CCxlPlQByIFBLlNlBlNqQGShJQkpiUDlAUiUJKBJJ"
                            "kyoiGUQCETR+sETZI/WCho2owVGJI/WCMOZ3qGnJSySm1N70tQQ2CKrurKdtSKc1EYnPKPUNXfyRVk7YK"
                            "aaZz2sDGOdrecBuBzJXgVbfTPXGYscKlkgdJJnm4dAOjeWyNVjXvj6una8sfURhw5t1DIXnvEN1rJKxzq"
                            "jMI1HsI3AZDenT7155PfriZ3EVj9DjvG8At92ENdc/hlJTskmjLqdznBrdXXuLj7BsOSmtxR3X8X11vrW"
                            "tbcHFmodo0NDwB1+dajhXjWa43umooqySqEz8GJ9NpIHV2rbGBv8AYvOrRRRVzHSP7GNodp1PPnOPXC2N"
                            "mpaOw6bnDpNU0EREO3BI7vDKEvXww4zuuXVXyjgeWsJlcOek4A+dYtt0q3wvmq6mSSV431O2HsA5KiarS"
                            "0vJzpBJ35qsY1N246obW0fCXRsc70Yxlzz8wWEu/wCVS7VExbbGRUsQ5FzA559+wWU7V00skrnZmlcS+R"
                            "wyT/4inp46iJzHACdo1Nc35QT+G1icbzgz8o1zrbpTW6407ar4Q8MbJC0Ne095HIjqeS9WDl81cJXnyBf"
                            "6S4uZqZE4tkA56XAh2PmK+jYJmSxtkjeHMcA5rgdiDyK1H2C+QsFJBrTawmSx6gaYoO0CEvTJPUJCVGXI"
                            "S9CXhMPUD1J1D2iSYeoYgXKQf4jvej8qSDlKfeso3iigI3s858JFI3im3dbRUD6anaq8bNS26yfpDnxUr"
                            "bvJ1kKyjeJ6Fw2s9WR7HqQcRUWMmyVuO/JU61ONms8qyhue0TC8S+uVkW8V2pxwLfUn2CQFSM4qtbDk22"
                            "qH0k61ONmkuNfNV22rhZN2bnxOAeemy8gkJmL5d8udsT3Bb9vFdmedDqOpbr2yXDG6xT4+ypmsJBcwnfO"
                            "x84/gszeJ/DrSk1j65b3DWO5RTuDp8gdOSOb0lAXfnAT3I0lpal8OzHED2ErrU93lc1rHyEhnIErhaSOh"
                            "RMfp33B6pqNVFe3Pj8526I3bzT53RZaOUgkA536KUTO701VyOoYwFpGWkbYRMnBlbpyNsFVX08npwtc+M"
                            "925HsKNgdGxzpRpONh/Uqx8c7V1RHQ9cBew8H3upj4WtzZMktjLQT1aHED7MLyOlhFTUhhdoYTlz8Z0t6"
                            "nC9NhvvC8FNFBFNViOJoY0CLoEreK/kvSbR8ac3+THco3cQS9FnHcQcOdJq0fwkIv3DhP95rPqlrrVz42"
                            "aUX+Ugnu9ib+0MuN1m/L3Dg51VYP4SRvnDjhgVNXy/QlOsLxlohxC8pjxA9Zvyzw4P81V/UH8EPlvhv8A"
                            "W6r6g/gr1qnGzR/2heks55Z4c/Xqr/bn8Ek61ONm2lFthOmV8Id6o3PuG6ZnYuGKahlkHrOj7Nv/ACx9y"
                            "vwwwwj81FHGO5jQFLtnOyxjo5rqOql9FtNTDvDO1d9uB96lda2SsDamaSZvqk6Gn5m4yr45Ig3vTBSbb4"
                            "Ym6YIo4+4Ma0KT4FGQMsacDqFZfJFG0l72gDnkrP1/EsfaGC2RPq6jOPMHmjxKhETLpTwUcEbpJY4msaM"
                            "lxaBheecTMst6D57W2eOdh0uljjBjd83U+C1jbNPXt7e/TmoIGWUw2iafaOq5s8Qa/HZxlg5NAwAktQ83"
                            "qbFMJMQzdr7DEWfeqtTZK6Fmp8Od9OzgvRo6CIyF3ZtBPMkqV9ut4ID2En9lxWGvjzWnt0+NMlJLqH7RG"
                            "3grtot1WythMbW69Q0GVuW59y2M1NTa2mNr9ttxnIUkVukErZGs0lvouSVTHhi81hD65lqkJbzfCPwWa4"
                            "m4Kbba6OOCsjiim3jMxJaD3F3MeJC20j6qVuRUO2AGNlyrlQVNY1zKlrp4yOrtx4JGQz9YmXhu9UB1MfR"
                            "vB2zHWR/9iFUq7fXEZnPmj5OppAP0ditZS0LKeodS3EOaT8TKDsfFWKq2SU+GjXy5txg/YtaqjwLwtc5b"
                            "jT10bo44YzlznkO1N6t08zkbL1dtpoydqaMeDV5xYQ+mu0TiHaS7zvBenRPZI3LWn3rUMWmdRG3RtHmMZ"
                            "9NvNRupYmfGUQcOpj0n8CrulvqH3ogQOiuM65bm2kuEcggY8/IlGg+44QT2G1VDfztFA8H92F054op2Fk"
                            "0bJGEYLXtBBXPFogiOaR89Mf3UpA/l5JkGy5NRwRw/NzpNH+m9zfuK5VR+Tq2OdmGqqY/2cg/0WpkjukX"
                            "xVRDO0fJlZg+8KEXOph2rbfJz9OHzh+KnmF9T+2V/+dUX6/P/AChJazy3Rd8n1ZSU8wvqf2s6x0UL6h7T"
                            "6OyKWeOMZJC4ly4gipwWtILjyCqOo64vbuGgD2lUK/ieGmYWg65ejWrP9rX3N5DcxRn3rsW3h+CHDnjU/"
                            "vKjXxSjhud+kzUyOhp/UaefitPbLbBb4gynjDT1djcqWGDsx5gACtMyAqkyGo2gPfhZKoc90h0jqtdKfM"
                            "IKzVRRyGUlveqimYZsA5wEGJg7fdo7guj8HdpwSm0aBjGVMNVo4yemfapxHIRsdksuGwGynieSRkJi6ri"
                            "CbOybROXY1HC6o3HJV5WYOQpi+lCstYrYCyXn0PcqVLVSUThRVvnNHxcjhz9i65e8dVSuFMKyEgjzlJg1"
                            "ZghjkIka1uR1AWjoXYj06lhrZVyUM3YTk6c7ErW0krXtDmvByrCTDrFxTZVdrzhEJO9aZSkoS7CDWhLlA"
                            "Tn7KNzkxchL1Q2G+q33J0Oop0GBkrK2vfhmpreSvW+yZIfLlzjzJStfILRQeiFG0dLSshGA1XACEzeak6"
                            "JiDjeVOHKsxSjkiHkOQqT2jKtu5Kq7mgiLVBJHurRUT1RW7JSxRIgpo0QQaQFDKwlWuiiciqmg9UTYkZR"
                            "MUWHNuVsbNHqaMOVK110lFN2E/IciVo3fFlZW7/HjxUVsYKpkrAWkIid1xLT8W1dlq0wmDtkxKDokUDOK"
                            "AuTlAUUWpJAkg//Z")
        image = OfflineImage(data=base64_image_str)

        # Apply various image transformations
        image.resize_image_custom((800, 600), cv2.INTER_LANCZOS4)
        image.rotate_image(45)
        image.crop_image((50, 50, 750, 550))
        image.convert_to_grayscale()
        image.apply_blur((5, 5))

        # Save the final image to disk
        image.save_image_to_disk("./test_data/images/processed_image.png")

        print("OfflineImage processing and saving completed successfully.")

    except Exception as e:
        print(f"An exception occurred during testing: {e}")
        return False

    return True


if __name__ == "__main__":
    local_test()
from inspect import stack
from PIL import Image
import requests
import os
import re
from urllib.parse import urlparse, urljoin
import base64
import warnings
from typing import Type, Union, Tuple, Optional, List
import warnings
from requests import Session


class ImageManager:
    def __init__(self, base_location: Optional[str]=None):
        self.base_location = base_location
        self.images: List[Union[OfflineImage, OnlineImage]] = []
        
    def add(self, ImageClass: Type[Union['OfflineImage', 'OnlineImage']], *args, **kwargs) -> int:
        self.images.append(ImageClass(*args, **kwargs))
        return len(self.images) - 1

    def remove(self, index: int):
        del self.images[index]

    def execute(self, index: int, function, *args, **kwargs):
        getattr(self.images[index], function)(*args, **kwargs)

class OfflineImage:
    def __init__(self, data: Optional[Union[str, bytes]]=None, path: Optional[str]=None):
        if data is not None and path is None: self.data = data
        elif path is not None and data is None: self.get_data(path)
        else: warnings.warn(
                    "Please pass exactly one argument to the init method. This behaviour is deprecated and will be removed in version 0.1.4.0.",
                    DeprecationWarning,
                    stacklevel=2
                    )
        
    def get_data(self, path: str):
        with open(path, 'rb') as f:
            self.data = f.read()

    def _save_image(self, source_path: str, img_data: bytes, new_name: Optional[str]=None) -> Optional[str]: # Optional[str] from typing import Optional
        if source_path.split(".")[-1] == 'svg':
            print("SVG format is not supported.")
            return None
        with open(source_path, 'wb') as img_file:
            img_file.write(img_data)
        return self._convert_image_format(source_path, new_name) if new_name else source_path
    
    def save_image(self, base_location: str, img_data: bytes, original_name: str, original_format: Optional[str]=None, new_name: Optional[str]=None, target_format: Optional[str]=None) -> Optional[str]: # Optional[str] from typing import Optional
        if original_format == '.svg':
            print("SVG format is not supported.")
            return None
        source_path = os.path.join(base_location, f"{original_name}.{original_format}" if original_format else original_name)
        with open(source_path, 'wb') as img_file:
            img_file.write(img_data)
        return self.convert_image_format(base_location, original_name, original_format, new_name, target_format)
            
    def _convert_image_format(self, source_path, new_name) -> Union[None, str]: # Optional[str] from typing import Optional
        if source_path.split(".")[-1] == "svg":
            print("SVG format is not supported.")
            return None
        # Create the new file path with the desired extension
        new_file_path = os.path.join(os.path.dirname(source_path), f"{new_name}")
        # Open, convert and save the image in the new format
        with Image.open(str(source_path)) as img:
            img.save(new_file_path)
        os.remove(source_path) if source_path != new_file_path else print("Skipping deleting ...")
        return new_file_path
        
    def convert_image_format(self, base_location: str, original_name: str, original_format: Optional[str]=None, new_name: Optional[str]=None, target_format: Optional[str]='png') -> Optional[str]: # Optional[str] from typing import Optional
        source_path = os.path.join(base_location, f"{original_name}.{original_format}" if original_format else original_name)
        if source_path.split(".")[-1] == "svg":
            print("SVG format is not supported.")
            return None
        # Extract the base file name without extension
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        # Create the new file path with the desired extension
        if new_name is None:
            new_file_path = os.path.join(os.path.dirname(source_path), f"{base_name}.{target_format}")
        else:
            new_file_path = os.path.join(os.path.dirname(source_path), f"{new_name}.{target_format}")
        # Open, convert and save the image in the new format
        with Image.open(str(source_path)) as img:
            img.save(new_file_path)
        os.remove(source_path) if source_path != new_file_path else print("Skipping deleting ...")
        return new_file_path

    def base64(self, path: str, new_name: str, img_format: str, data: Optional[str]=None) -> bool:
        internal_data = self.data if not data else data
        try:
            img_data = base64.b64decode(internal_data.split(',')[1])
            img_name = new_name + '.' + img_format
            source_path = os.path.join(path, img_name)
            if self._save_image(source_path, img_data, img_name) is None: return False
        except: return False
        return True

class OnlineImage(OfflineImage):
    def __init__(self, current_url: Optional[str]=None, session: Optional[Session]=None, one_time: bool=False):
        self.current_url = current_url
        if one_time == True:
            self.download_image(".\\")
            
    def download_logo_image(self, base_path: str, new_name: str, img_format: str) -> bool:
        warnings.warn(
            "download_logo_image is deprecated here and will be moved in version 0.1.4.0. Use OfflineImage.base64 or OnlineImage.download_image instead.",
            category=DeprecationWarning,
            stacklevel=2
        )
        if self.current_url is not None: img_url = self.current_url
        else: return False
        try:
            format_match = re.match(r'^data:image/[^;]+;base64,', img_url)
            if format_match:
                if "image/svg+xml" in img_url:
                    print("SVG format is not supported.")
                    return False
                return self.base64(base_path, new_name, img_format, data=img_url)
            else:
                return self.download_image(base_path, img_url, new_name, img_format)[0]
        except:
            return False
            
    def download_image(self, basepath: str, new_img_url: Optional[str]=None, new_name: Optional[str]=None, img_format: Optional[str]=None) -> Union[Tuple[bool, None, None], Tuple[bool, str, str]]:
        if self.current_url is None: return False, None, None
        try:
            img_url = urljoin(self.current_url, "") if not new_img_url else new_img_url
            img_name: str = os.path.basename(urlparse(img_url).path)
            name = img_name.split(".")[0] if not new_name else new_name
            extension = None
            try: extension = img_name.split(".")[-1] if not img_format else img_format
            except: pass
            
            if img_name.strip():
                response = requests.get(img_url) # verify=False
                response.raise_for_status()
                img_data = response.content
                print(f"Downloaded image {img_name}.")
                self._save_image(os.path.join(basepath, f"{name}.{extension}"), img_data, new_name=None)
                return True, f"{name}.{extension}", os.path.join(basepath, f"{name}.{extension}")
            else:
                return False, f"{name}.{extension}", os.path.join(basepath, f"{name}.{extension}") # Passing it here, so it can be deleted if created
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
            print(f"An unexpected error occurred: {e}")
        return False, None, None
            
def local_test():
    try:
        from aplustools.io.environment import Path

        # Download the image to the current working directory
        OnlineImage("https://www.simplilearn.com/ice9/free_resources_article_thumb/what_is_image_Processing.jpg", True)

        # Makeing sure the folder_path exists
        folder_path = Path(".\\test_data\\images")
        folder_path.create_directory()

        # Converting the image and moving it to a specified path
        image = OfflineImage("data:image/jpeg;base64,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")
        success = image.base64(str(folder_path), "Image", "png") # Make sure this directory exists

        # Downloading the image to a specified path
        image2 = OnlineImage("https://www.simplilearn.com/ice9/free_resources_article_thumb/what_is_image_Processing.jpg")
        _, img_path, img_name = image2.download_image(str(folder_path))
    except Exception as e:
        print(f"Exception occured {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True

if __name__ == "__main__":
    local_test()

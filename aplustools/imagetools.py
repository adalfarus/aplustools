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
            
from PIL import Image as Image
import requests
import os
import re
from urllib.parse import urlparse, urljoin
import base64
import warnings
from typing import Type, Union


class ImageManager:
    def __init__(self, base_location: str):
        self.base_location = base_location
        self.images = []
        
    def add(self, ImageClass: Type[Union['OfflineImage', 'OnlineImage']], *args, **kwargs):
        self.images.append(ImageClass(*args, **kwargs))
        return len(self.images) - 1

    def remove(self, index: int):
        del self.images[index]

    def execute(self, index: int, function, *args, **kwargs):
        getattr(self.images[index], function)(*args, **kwargs)

class OfflineImage:
    def __init__(self, data: str=None, path: str=None):
        if data is not None and path is None: self.data = data
        elif path is not None and data is None: self.get_data(path)
        else: print("Please pass exactly one argument to the init method.")
        
    def get_data(self, path: str):
        with open(path, 'rb') as f:
            self.data = f.readlines()

    def _save_image(self, source_path: str, img_data: str, new_name: str=None):
        if source_path.split(".")[-1] == 'svg':
            print("SVG format is not supported.")
            return None
        with open(source_path, 'wb') as img_file:
            img_file.write(img_data)
        return self._convert_image_format(source_path, new_name) if new_name else source_path
    
    def save_image(self, base_location: str, img_data: str, original_name: str, original_format: str=None, new_name: str=None, target_format: str=None):
        if original_format == '.svg':
            print("SVG format is not supported.")
            return None
        source_path = os.path.join(base_location, f"{original_name}.{original_format}" if original_format else original_name)
        with open(source_path, 'wb') as img_file:
            img_file.write(img_data)
        return self.convert_image_format(base_location, original_name, original_format, new_name, target_format)
            
    def _convert_image_format(self, source_path, new_name):
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
        
    def convert_image_format(self, base_location: str, original_name: str, original_format: str=None, new_name: str=None, target_format: str='png'):
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

    def base64(self, path: str, new_name: str, img_format: str, data: str=None):
        internal_data = self.data if not data else data
        img_data = base64.b64decode(internal_data.split(',')[1])
        img_name = new_name + '.' + img_format
        source_path = os.path.join(path, img_name)
        self._save_image(source_path, img_data, img_name)

class OnlineImage(OfflineImage):
    def __init__(self, current_url: str=None, one_time: bool=True):
        self.current_url = current_url
        if one_time == True:
            self.download_image(".\\")
            
    def download_logo_image(self, img_url: str, new_name: str, img_format: str):
        warnings.warn(
            "download_logo_image is deprecated and will be removed in version 1.4.0. Use OfflineImage.base64 or OnlineImage.download_image instead.", 
            category=DeprecationWarning,
            stacklevel=2
        )
        try:
            format_match = re.match(r'^data:image/[^;]+;base64,', img_url)
            if format_match:
                if "image/svg+xml" in img_url:
                    print("SVG format is not supported.")
                    return False
                return self.base64(img_url, new_name, img_format)
            else:
                return self.download_image(".\\data", img_url, new_name, img_format)
        except:
            return
            
    def download_image(self, basepath: str, img_url: str=None, new_name: str=None, img_format: str=None):
        try:
            img_url = urljoin(self.current_url, "") if not img_url else img_url
            img_name = os.path.basename(urlparse(img_url).path)
            print(f"Downloaded image {img_name}.")
            name = img_name.split(".")[0] if not new_name else new_name
            extension = None
            try: extension = img_name.split(".")[-1] if not img_format else img_format
            except: pass
            
            if img_name.strip():
                response = requests.get(img_url) # verify=False
                response.raise_for_status()
                img_data = response.content
                self._save_image(os.path.join(basepath, f"{name}.{extension}"), img_data, new_name=None)
                return True
            else:
                return False
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
            
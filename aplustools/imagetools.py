from PIL import Image
import requests
import os
import re
from urllib.parse import urlparse, urljoin
import base64

class ImageManager:
    def __init__(self, base_location):
        self.base_location = base_location
        self.images = []
        
    def add(self, ImageClass, **args):
        self.images.append(ImageClass(**args))
        return len(self.images)

    def remove(self, index):
        del self.images[index]

    def execute(self, index, function, **args):
        self.images[index].function(**args)

class OnlineImage:
    def __init__(self, current_url=None, one_time=True):
        self.current_url = current_url
        if one_time == True:
            self.download_logo_image(current_url)
        
    def save_image(self, base_location, img_data, original_name, original_format=None, new_name=None, target_format=None):
        if original_format == '.svg':
            print("SVG format is not supported.")
            return None
        source_path = os.path.join(base_location, f"{original_name}.{original_format}" if original_format else original_name)
        with open(source_path, 'wb') as img_file:
            img_file.write(img_data)
        return self.convert_image_format(source_path, new_name, target_format) if target_format else source_path
            
    def convert_image_format(self, source_path, new_name=None, target_format='png'):
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
            
    def download_logo_image(self, img_url, new_name, img_format):
        try:
            format_match = re.match(r'^data:image/[^;]+;base64,', img_url)
            if format_match:
                if "image/svg+xml" in img_url:
                    print("SVG format is not supported.")
                    return False
                img_data = base64.b64decode(img_url.split(',')[1])
                img_name = new_name + '.' + img_format
                source_path = os.path.join(self.data, img_name)
                with open(source_path, 'wb') as img_file:
                    img_file.write(img_data)
            else:
                response = requests.get(img_url, verify=False, timeout=5)
                response.raise_for_status()
                img_name = os.path.basename(urlparse(img_url).path)
                source_path = os.path.join(self.data, img_name)
                img_data = response.content
                with open(source_path, 'wb') as img_file:
                    img_file.write(img_data)
            if img_name.strip():
                self._convert_image_format(source_path, new_name, img_format)
                return True
            else:
                return False
        except KeyError:
            print("The image tag does not have a src attribute.")
            return False
            
    def download_image(self, img_tag):
        try:
            img_url = urljoin(self.current_url, img_tag['src'])
            img_name = os.path.basename(urlparse(img_url).path)
            print(img_name)
            name = img_name.split(".")[0]
            extension = None
            try: extension = img_name.split(".")[1]
            except: pass
            
            if img_name.strip():
                img_data = requests.get(img_url, verify=False).content
                self.save_image(self.cache, img_data, name, extension, new_name=None, target_format=None)
        except KeyError:
            print("The image tag does not have a src attribute.")
        except Exception as e:
            print(f"An error occurred while downloading the image: {e}")
            
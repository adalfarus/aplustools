# aplustools
[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![Build Status](https://github.com/Adalfarus/aplustools/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: GPL-3.0](https://img.shields.io/github/license/Adalfarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)

## Description

aplustools is a simple, user-friendly Python library for performing amazing tasks. It simplifies complex processes, allowing you to achieve more with less code. Developed with a focus on ease of use and efficiency, aplustools is the go-to solution for Python developers looking to enhance their projects.

## Features

- Easy to use
- Highly efficient
- Supports multiple platforms
- Regular updates and support
- Comprehensive documentation

## Installation

You can install aplustools via pip:

```sh
pip install aplustools
```

Or clone the repository and install manually:

```sh
git clone https://github.com/Adalfarus/aplustools.git
cd aplustools
python -m build
```

## Usage

Here are a few quick examples of how to use aplustools:

### Search Engine usage
```python
from aplustools.web import new_webtools as wt

# Call the `google_search` function with a query
result = wt.search.google_provider.google_search("Cute puppies", wt.get_useragent(), 1)

# Print the result
print(result)
```

### Search Engine usage 2
```python
from aplustools.web import webtools as wt

# Call the `google_provider` function with a query
searcher = wt.Search()
result = searcher.google_provider("Cute puppies")

# Print the result
print(result)
```

### Logger
```python
from aplustools.io import environment as env
from aplustools.io import loggers

# Set the current working directory to the main script or executable
env.set_working_dir_to_main_script_location()

# Create an instance of Logger
p_logger = loggers.PrintLogger("my_logs_file.log", show_time=True, capture_print=False, 
                     overwrite_print=True, print_passthrough=False, print_log_to_stdout=True)
# Shows the time in the logs (Like this [12:33:21]) and overwrites the normal sys.stdout

# Call the `monitor_stdout` method and pass the logger object, this will overwrite sys.stdout from Text I/O to the logger object
logger = loggers.monitor_stdout(logger=p_logger) # Return sys.stdout, so you can make sure it worked

# Log something
p_logger.log("Hello, world!")

# Print something, it won't get captured or displayed
print("Hello, beautiful world!")

# Close the Logger object (returns sys.stdout to it's normal state)
p_logger.close()
```

### OnlineImage
```python
from aplustools.utils import imagetools
from aplustools.io.environment import Path

# Download the image to the current working directory
imagetools.OnlineImage("someImage.url", True)

# Making sure that folder_path exists
folder_path = Path(".\\images")
folder_path.create_directory()

# Converting the image and moving it to a specified path
image = imagetools.OfflineImage("data:image/jpeg;base64,/9j...")
success = image.base64(str(folder_path), "Image", "png") # Make sure this directory exists

# Download the image to a specified path
image2 = imagetools.OnlineImage("someImage.url")
_, img_name, img_path = image2.download_image(base_path=str(folder_path))  # Make sure this directory exists
```

### Git-Updater
```python
from aplustools.data import updaters
from aplustools.io.environment import set_working_dir_to_main_script_location, Path
import os
import threading
import sys

set_working_dir_to_main_script_location()

__version__ = updaters.vNum("0.0.1")

# Initialize an updater
updater = updaters.gitupdater("exe")
latest_version = updater.get_latest_version("Adalfarus", "unicode-writer")[1]  # Gives back two values, use whichever applicable

# Check if an update is needed
if __version__ >= updaters.vNum(latest_version):
    sys.exit()

# Define the arguments for the updater method
host, port, path = "localhost", 1264, Path(os.path.join(updaters.get_temp(), "update"))
gui_toggle, cmd_toggle = False, False
path.create_directory()
update_args = (os.path.join(os.getcwd(), "update"), str(path),
                latest_version, "Adalfarus", "unicode-writer", gui_toggle, cmd_toggle, host, port)

# Start the update in a separate thread
update_thread = threading.Thread(target=updater.update, args=update_args)
update_thread.start()

# Receive the update status generator and print them
progress_bar = 1
for i in updater.receive_update_status(host, port):
    print(f"{i}%", end=f" PB{progress_bar}\n")
    if i == 100:
        progress_bar += 1  # Switch to second progress bar, when the downloading is finished
```

### Webtools
```python
... # Continuing the first two examples

# Print the result
print(result)

from aplustools.web.webtools import check_url, is_crawlable
import requests

if check_url(result, ''): # Not really nessesary, search does this automatically
	response = requests.get(result)
	...
```

### Environment
```python
... # Continuing the image example

_, img_name, img_path = image2.download_image(base_path=str(folder_path))  # Make sure this directory exists

from aplustools.io.environment import absolute_path, remv, copy
from aplustools.childsplay import ImportClass  # Could be switched out to adultswork, but the string would need to get converted

importer = ImportClass(hard=True)
importer.import_all()  # Destroys your runtime python

a_img_path = absolute_path(img_path)

try:
    copy(a_img_path, str(folder_path) + str(img_name).remove(".png") + str(" - Copy.png"))
except ValueError:
    copy(a_img_path, str(folder_path) + str(img_name.split(".")[-1]) + str(" - Copy.png"))

remv(a_img_path)  # Remove the original image
remv(str(folder_path))  # Remove the base directory
```

### Faker
```python
from aplustools.data.faker import TestDataGenerator

test_data = TestDataGenerator()
print(test_data.generate_random_identity())

print("\n", end="")
print(test_data.generate_random_name())
print(test_data.generate_random_email())
print(test_data.generate_random_password())
print(test_data.generate_random_phone_number())
print(test_data.generate_random_address())
print(test_data.generate_random_birth_date())
```

### Dummy
```python
from aplustools.utils.dummy import Dummy3 # Dummy3 is for Python 3
import math, sys

dummy = Dummy3()

# Do a bunch of operations that would normally throw errors
dummy.attr.func("", int3="")
dummy["Hello"]
del dummy[1]
reversed(dummy)
"Dummy" in dummy
dummy.keys()
dummy.keys = ["1"]
print(dummy.keys + dummy)
+dummy
-dummy
~dummy

hash(dummy)
abs(dummy)
round(dummy)
complex(dummy)
oct(dummy)
repr(dummy)
bytes(dummy)
format(dummy, "DD")

math.trunc(dummy)
dummy << dummy
dummy >> dummy
dummy -= 1_000_000
num = 1
num *= dummy

if dummy:
	print(True)
else:
	print(False)

for x in dummy:
	print(x)

type(dummy)
print(dummy, "->", int(dummy), list(dummy), tuple(dummy), float(dummy))
```

### Hasher
```python
from aplustools.utils.hasher import hashed_latest, hashed_wrapper_latest, reducer, big_reducer, num_hasher

inp = "Hello beautiful world, how are you today, lovely star?"
inp2 = "Hello World, kitty"

desired_length = 64

hashed_inp = hashed_wrapper_latest(inp, desired_length, hash_func=hashed_latest)
hashed_inp2 = hashed_wrapper_latest(inp2, desired_length, hash_func=hashed_latest)

print(f"{inp} ({len(inp)}) -> {hashed_inp} ({len(hashed_inp)})\n{inp2} ({len(inp2)}) -> {hashed_inp2} ({len(hashed_inp2)})")

num_hashed_inp = num_hasher(inp, desired_length)
num_hashed_inp2 = num_hasher(inp2, desired_length)

print(f"{inp} ({len(inp)}) -> {num_hashed_inp} ({len(num_hashed_inp)})\n{inp2} ({len(inp2)}) -> {num_hashed_inp2} ({len(num_hashed_inp2)})")

acceptable_chars = range(100, 200)

num_hashed_inp_uni = num_hasher(inp, desired_length, acceptable_chars)
num_hashed_inp_uni = num_hasher(inp2, desired_length, acceptable_chars)

print(f"{inp} ({len(inp)}) -> {num_hashed_inp_uni} ({len(num_hashed_inp_uni)})\n{inp2} ({len(inp2)}) -> {num_hashed_inp_uni} ({len(num_hashed_inp_uni)})")
```

### GenPass
```python
from aplustools.utils.genpass import GeneratePasswords

gen = GeneratePasswords(debug=True)
password = gen.generate_ratio_based_password_v2(length=10, letters_ratio=0.5, numbers_ratio=0.3, punctuations_ratio=0.2, secure_random=True, exclude_similar=True)
print(password)
```

### web_requests
```python
from aplustools.web.web_request import UnifiedRequestHandler, UnifiedRequestHandlerAdvanced

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

folder_path = "../test_data/images"
os.makedirs(folder_path, exist_ok=True)

# Synchronous binary request (e.g., image)
image_content = adv_handler.request('GET', 'http://example.com/image.png', async_mode=False, return_type='binary')
with open(os.path.join(folder_path, './image.png'), 'wb') as file:
    file.write(image_content)

# Asynchronous binary request (e.g., image)
image_content_async = adv_handler.request('GET', 'http://example.com/image.png', async_mode=True, return_type='binary')
with open(os.path.join(folder_path, './image_async.png'), 'wb') as file:
    file.write(image_content_async)
```
(Correct shortform for aplustools is apt, so please use ```import aplustools as apt``` for consistency)

There are multiple clis added through this package:

### pype (python pipe)
```bash
C:\Users\user_>pype
Enter Python expression: 1+2
3

C:\Users\user_>pype 1// 3
0
```
### upype (unified python pipe)
```bash
C:\Users\user_>upype import aplustools; print(aplustools.__version__)
1.4.4

C:\Users\user_>upype
Enter Python code (type 'end' on a new line to finish):
... class Test:
...     def hello_word(self):
...             print("Hello, ya dunce!")
... test = Test()
... test.hello_word()
... end
Hello, ya dunce!
```
### run_apt_tests
Will run the aplustools tests using pytest. For me it causes an error at the moment because of a strange error with asyncio, so maybe it won't work.


For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and more
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

Dependencies (except for the standart libraries) are: 
- data.database, io.environment, io.loggers, utils.mappers, data.faker, utils.dummy, utils.hasher, package.lazy_loader, package.timid, adultswork, childsplay - none
- data.gitupdater-cmd & data.integrated-gitupdater-cmd - requests
- data.gitupdater-gui & data.integrated-gitupdater-gui - requests, PySide6
- data.gitupdater, data.updaters - requests
- data.imagetools - Pillow, asyncio, aiohttp, requests
- data.upgraded_imagetools - opencv-python, asyncio, aiohttp
- web.webtools - requests, duckduckgo_search, BeautifulSoup4 - duckduckgo_search is only used for Search.duckduckgo_provider, if you don't want to use it, use Search._duckduckgo_provider instead.
- utils.genpass - pycryptodome, rich
- web.new_webtools, web.actual_webtools - requests, BeautifulSoup4
- web.web_request - requests, asyncio, aiohttp

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

aplustools is licensed under the GPL-3.0 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.

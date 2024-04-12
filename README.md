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
from aplustools.web.search import Search, GoogleSearchCore

# Call the `google_provider` function with a query
searcher = Search(GoogleSearchCore(advanced=True))
results = searcher.search("Cute puppies", num_results=10)

# Print the result
print(results)

from aplustools.web.utils import WebPage

web_page = WebPage(results[0].get("url"))

response = None
if web_page.crawlable:  # Google search does this automatically at the moment
    response = web_page.page.content
print(response)

```

### web requests
```python
from aplustools.web.request import UnifiedRequestHandler, UnifiedRequestHandlerAdvanced
import os

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
image_content = adv_handler.request('GET', 'http://example.com/image.png', async_mode=False, return_type='binary')
with open(os.path.join(folder_path, './image.png'), 'wb') as file:
    file.write(image_content)

# Asynchronous binary request (e.g., image)
image_content_async = adv_handler.request('GET', 'http://example.com/image.png', async_mode=True, return_type='binary')
with open(os.path.join(folder_path, './image_async.png'), 'wb') as file:
    file.write(image_content_async)

```

### ImageManager
````python
from aplustools.data.imagetools import ImageManager, OnlineImage
import os

os.makedirs("./test", exist_ok=True)
manager = ImageManager("./test", use_async=True)
image_index = manager.add_image(OnlineImage, "somewhere.com/image.jpg")

manager.execute_func(image_index, "download_image")
manager.execute_func(image_index, "convert_to_grayscale")
manager.execute_func(image_index, "apply_filter")  # Default is blur
manager.execute_func(image_index, "rotate_image", 12)
manager.execute_func(image_index, "save_image_to_disk")  # Overwrites downloaded file

````

### ImageTypes
```python
from aplustools.data.imagetools import OnlineImage, OfflineImage, ImageFilter, SVGCompatibleImage
import os

# Setup
folder_path = "./images"
os.makedirs(folder_path, exist_ok=True)
test_url = "someImage.url"
base64_image_str = ("data:image/jpeg;base64,...")

# Test downloading an online image
online_image = OnlineImage(current_url=test_url, base_location=folder_path, one_time=True)
download_result = online_image.download_image(folder_path, online_image.current_url, "downloaded_image", "jpg")
if not download_result[0]:
    raise Exception("Failed to download image.")
else:
    online_image.convert_to_grayscale()
    online_image.save_image_to_disk(os.path.join(folder_path, "image.png"))

# Test loading and saving a base64 image with OfflineImage
offline_image = OfflineImage(data=base64_image_str, base_location=folder_path)
save_result = offline_image.base64(folder_path, "base64_image", "png")
if not save_result:
    raise Exception("Failed to save base64 image.")

# Test image transformations
offline_image.resize_image((100, 100))
offline_image.rotate_image(45)
offline_image.convert_to_grayscale()
offline_image.apply_filter(ImageFilter.BLUR)
offline_image.save_image_to_disk(os.path.join(folder_path, "transformed_image.png"))

# Example svg image usage
image_processor = SVGCompatibleImage("someSvg.svg", 300,
                                     (667, 800), magick_path=r".\ImageMagick",
                                     base_location='./')
image_processor.save_image_to_disk()


from aplustools.io.environment import absolute_path, remv, copy

a_img_path = absolute_path(os.path.join(folder_path, "downloaded_image.jpg"))

copy(a_img_path, str(folder_path) + "downloaded_image" + " - Copy.jpg")

remv(a_img_path)  # Remove the original image
remv(folder_path)  # Remove the base directory

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
from aplustools.utils.dummy import Dummy3  # Dummy3 is for Python 3
import math

dummy = Dummy3()

# Do a bunch of operations that would normally throw errors
dummy.attr.func("", int3="")
dummy["Hello"] = 1
del dummy[1]
reversed(dummy)
if not "Dummy" in dummy:
    dummy.keys = ["1"]
print(dummy.keys + dummy)
var1 = +dummy
var2 = -dummy
var3 = ~dummy
print(var1, var2, var3)

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
num_hashed_inp_uni_2 = num_hasher(inp2, desired_length, acceptable_chars)

print(f"{inp} ({len(inp)}) -> {num_hashed_inp_uni} ({len(num_hashed_inp_uni)})\n{inp2} ({len(inp2)}) -> {num_hashed_inp_uni_2} ({len(num_hashed_inp_uni_2)})")

```

### GenPass
```python
from aplustools.utils.genpass import SecurePasswordManager, GeneratePasswords

manager = SecurePasswordManager()
password = manager.generate_ratio_based_password_v2(length=26, letters_ratio=0.5, numbers_ratio=0.3,
                                                    punctuations_ratio=0.2, exclude_similar=True)
manager.add_password("example.com", "json-the-greatest", password)
manager.store_in_buffer("example.com", 0)  # Stores unencrypted password in a buffer
print(manager.get_password("example.com"), "|", manager.use_from_buffer(0))  # for faster access.

print(GeneratePasswords.generate_custom_sentence_based_password_v1(
    "Exploring the unknown -- discovering new horizons...", random_case=True, extra_char="_",
    char_position="keep" or 0, num_length=5, special_chars_length=2))
# "keep" just sets it to 0

# These classes are mostly meant for secure interprocess bidirectional
# communication using networks.
from aplustools.utils.genpass import ControlCodeProtocol, SecureSocketServer, SecureSocketClient

# Initialize the protocol
prot = ControlCodeProtocol()

# Create a client and a server
client = SecureSocketClient(prot)
sock = client.get_socket()
server = SecureSocketServer(sock, prot)

# Start key exchange and communication between server and client
client.start_and_exchange_keys()  # Client has to start first
server.start_and_exchange_keys()

# Client sends a message and a control code to the server
client.add_control_code("shutdown")
client.add_message("HELLO SERVER")
client.sendall()  # The message is still received as it sends one chunk here
# which then get's decoded in one piece. The decoder decodes everything
# into chunks and control codes are always put behind messages.

# Server shuts down the client connection
server.shutdown_client()
print("DONE1")

# There are also classes for one directional communication that are
# more integrated.
from aplustools.utils.genpass import ControlCodeProtocol, ServerMessageHandler, ClientMessageHandler
import threading

prot = ControlCodeProtocol()

# Create message handlers for server and client
encoder = ClientMessageHandler(prot)

# Make a connection using the clients host and chosen port
connection = encoder.get_socket()

decoder = ServerMessageHandler(connection, prot)

# Client prepares and sends a message
encoder.add_message("Hello Server")
encoder.send_control_message("shutdown")

# Server receives and processes each chunk
encoder.start()
threading.Thread(decoder.listen_for_messages()).start()  # Blocking
encoder.flush()  # Blocking until connection is established

```

### Github-Updater
```python
from aplustools.data.updaters import GithubUpdater, VersionNumber
from aplustools.io.environment import get_temp
from aplustools import set_dir_to_ex
import sys
import os

set_dir_to_ex()

__version__ = VersionNumber("0.0.1")

# Initialize an updater
updater = GithubUpdater("Adalfarus", "unicode-writer", "py")  # If you want to use exe
latest_version = updater.get_latest_tag_version()             # you need to compile them
                                                              # yourself, otherwise it
# Check if an update is needed                                # won't work
if __version__ >= latest_version:
    sys.exit()

# Updater method
path, zip_path = os.path.join(os.getcwd(), "update"), os.path.join(get_temp(), f"apt-update_{latest_version}")

os.makedirs(path, exist_ok=True)
os.makedirs(zip_path, exist_ok=True)

# Start the update in a separate thread
update_thread = updater.update(path, zip_path, latest_version, implementation="none", 
                               host="localhost", port=1264, non_blocking=True, wait_for_connection=True)
update_thread.start()

# Receive the update status generator and print them
progress_bar = 1
for i in updater.receive_update_status():
    print(f"{i}%", end=f" PB{progress_bar}\n")
    if i == 100:
        progress_bar += 1  # Switch to second progress bar, when the downloading is finished
update_thread.join()

```

### ArguMint
```python
from aplustools.package.argumint import ArgStruct, ArguMint
from typing import Literal
import sys


def sorry(*args, **kwargs):
    print("Not implemented yet, sorry!")


def help_text():
    print("Build -> dir/file or help.")


def build_file(path: Literal["./main.py", "./file.py"] = "./main.py", num: int = 0):
    """
    build_file
    :param path: The path to the file that should be built.
    :param num:
    :return None:
    """
    print(f"Building file {path} ..., {num}")


from aplustools.package import timid

timer = timid.TimidTimer()

arg_struct = {'apt': {'build': {'file': {}, 'dir': {'main': {}, 'all': {}}}, 'help': {}}}

# Example usage
builder = ArgStruct()
builder.add_command("apt")
builder.add_nested_command("apt", "build", "file")

builder.add_nested_command("apt.build", "dir", {'main': {}, 'all': {}})
# builder.add_subcommand("apt.build", "dir")
# builder.add_nested_command("apt.build.dir", "main")
# builder.add_nested_command("apt.build.dir", "all")

builder.add_command("apt.help")
# builder.add_nested_command("apt", "help")

print(builder.get_structure())  # Best to cache this for better times (by ~15 microseconds)

parser = ArguMint(default_endpoint=sorry, arg_struct=arg_struct)
parser.add_endpoint("apt.help", help_text)

parser.add_endpoint("apt.build.file", build_file)

sys.argv[0] = "apt"

# Testing
# sys.argv = ["apt", "help"]
# sys.argv = ["apt", "build", "file", "./file.py", "--num=19"]
parser.parse_cli(sys, "native_light")
print(timer.end())

```

### compressor
```python
from aplustools.data.compressor import FileContainerV3, BrotliChunkCompressor
import os


compressor = BrotliChunkCompressor()
container = FileContainerV3(compressor, block_size=2048*2048)

image_data = {}
for file in os.listdir("./images"):
    if file.lower().endswith(".png"):
        with open(os.path.join("./images", file), "rb") as f:
            image_file_data = b''.join(f.readlines())
            image_data[file] = image_file_data

for file_name, image in image_data.items():
    container.add_file(file_name, image)

# Get the compressed data
compressed_data = container.get_compressed_container()

print("Compression done")

with open("./files.bin", "wb") as f:
    f.write(compressed_data)

print("Wrote bin")

# To extract a specific file from the compressed data
try:
    decompressed_images = []
    for i in range(len(image_data)):
        decompressed_image = container.extract_file(compressed_data, i)
        decompressed_images.append(decompressed_image)
except Exception as e:
    print("Indexing not possible, error", e, "\n")
    decompressed_images = []
    for file_name in image_data.keys():
        decompressed_image = container.extract_file(compressed_data, file_name)
        decompressed_images.append(decompressed_image)
compression_ratio = len(compressed_data) / sum(len(x) for x in image_data.values())

print(f"Original size: {sum(len(x) for x in image_data.values())} bytes")
print(f"Compressed size: {len(compressed_data)} bytes")
print(f"Compression ratio: {compression_ratio:.2f}")

for i, decompressed_image in enumerate(decompressed_images):
    with open(f"./decompressed_images/image{i}.png", "wb") as f:
        f.write(decompressed_image)

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

(Correct shortform for aplustools is apt, so please use ```import aplustools as apt``` for consistency)

There are multiple clis added through this package:

### pype (python pipe)
```bash
C:\Users\user_>pype
Enter Python expression: 1 + 2
3

C:\Users\user_>pype 1 // 3
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
...             print("Hello, you!")
... test = Test()
... test.hello_word()
... end
Hello, you!
```
### apt
Can currently run tests with ```apt tests run``` and show a basic help using ```apt help```.


For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and more
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

Dependencies (except for the standard libraries) are: 
- [`none`]
  - data.database
  - io.environment
  - io.loggers
  - data.faker
  - utils.dummy
  - utils.hasher
  - package.lazy_loader
  - package.timid
- [`requests`]
  - data.github-updater-none
  - data.updaters
  - data.github-updater-cmd
- data.github-updater-gui - [`requests`, `PySide6`]
- data.imagetools - [`Pillow`, `aiohttp`, `requests`, `wand`]
- data.advanced_imagetools - [`opencv-python`, `aiohttp`, `wand`, `pillow_heif`]
- web.search, web.utils - [`requests`, `BeautifulSoup4`]
- utils.genpass - [`cryptography`]
- web.request - [`requests`, `aiohttp`]
- utils.compressor - [`brotli`, `zstandard`, `py7zr`]
- io.gui - [`PySide6`]

Sub-Modules that may be removed in future updates due to being hard to support or simply unneeded.

- database (maybe unneeded and hard to support if more dbs are added -> new_database is being developed)
- loggers (maybe unneeded)

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

aplustools is licensed under the GPL-3.0 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.

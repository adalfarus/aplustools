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
python setup.py install
```

## Usage

Here are a few quick examples of how to use aplustools:

### Search Engine usage
```python
from aplustools import webtools as wt

# Call the `google_search` with a query
result = wt.search.google_provider.google_search("Cute puppies", wb.get_useragent(), 1)

# Print the result
print(result)
```

### Logger
```python
import aplustools.setdirtoex
# Just the import is needed to set the current working directory to the main script or executable
from aplustools import logs

# Create an instance of Logger
p_logger = logs.PrintLogger("my_logs_file.log", show_time=True, capture_print=False, 
                     overwrite_print=True, print_passthrough=False, print_log_to_stdout=True)
# Shows the time in the logs (Like this [12:33:21]) and overwrites the normal sys.stdout

# Call the `monitor_stdout` method and pass the logger object, this will overwrite sys.stdout from Text I/O to the logger object
logger = logs.monitor_stdout(logger=p_logger) # Return sys.stdout, so you can make sure it worked

# Log something
p_logger.log("Hello, world!")

# Print something, it won't get captured or displayed
print("Hello, beautiful world!")

# Close the Logger object (returns sys.stdout to it's normal state)
p_logger.close()
```

### OnlineImage
```python
from aplustools import imagetools
from aplustools.environment import Path

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
_, img_name, img_path = image.download_image(str(folder_path)) # Make sure this directory exists
```

### Git-Updater
```python
from aplustools import updaters
from aplustools.environment import set_working_dir_to_main_script_location
import os
import threading
from aplustools.environment import Path
import sys

set_working_dir_to_main_script_location()

__version__ = "0.0.1"

# Initialize an updater
updater = updaters.gitupdater("exe")
latest_version = updaters.get_latest_version("Adalfarus", "unicode-writer")[1] # Gives back two values, use whichever applicable

# Check if an update is needed
if not updaters.gitupdater.compare_release_numbers(__version__, latest_version):
	sys.exit()

# Define the arguments for the updater method
host, port, path = "localhost", 1264, Path(os.path.join(updaters.get_temp(), "update")
gui_toggle, cmd_toggle = False, False
path.create_directory()
update_args = (os.path.join(os.getcwd(), "update"), str(path), 
			latest_version, "Adalfarus", "unicode-writer", gui_toggle, cmd_toggle, host, port)

# Start the update in a seperate thread
update_thread = threading.Thread(target=updater.update, args=update_args)
update_thread.start()

# Receive the update status generator and print them
progress_bar = 1
for i in updater.receive_update_status(host, port):
	print(f"{i}%", end=f" PB{progress_bar}\n")
	if i == 100: progress_bar += 1 # Switch to second progress bar, when the downloading is finished
```

### Webtools
```python
... # Continuing the first example

# Print the result
print(result)

from aplustools.webtools import check_url, is_crawlable
import requests

if check_url(result, ''): # Not really nessesary, search does this automatically
	response = requests.get(result)
	...
```

### Environment
```python
... # Continuing the image example

_, img_name, img_path = image.download_image(str(folder_path)) # Make sure this directory exists

from aplustools.environment import absolute_path, remv, copy
from aplustools.childsplay import ImportClass # Could be switched out to adultswork, but the string would need to get converted

importer = ImportClass(hard=True)
importer.import_all() # Destroys your runtime python

a_imgpath = absolute_path(img_path)

try:
	copy(a_imgpath, str(folder_path) + str(img_name).remove(".png") + str(" - Copy.png"))
except ValueError:
	copy(a_imgpath, str(folder_path) + str(img_name.split(".")[-1]) + str(" - Copy.png"))

remv(a_imgpath) # Remove the original image
remv(str(folder_path)) # Remove the base directory
```
(Correct shortform for aplustools is apt, so use import aplustools as apt)

For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and more
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

Dependencies (except standart libraries) are: 
- adultswork - datetime
- childsplay - datetime
- database - none
- environment - none
- gitupdater-cmd - requests - deprecated
- gitupdater-gui - requests, pyqt5 - deprecated
- gitupdater - requests
- imagetools - Pillow
- logs - none
- setdirtoex - none
- updaters - requests
- webtools - duckduckgo_search, bs4 - duckduckgo_search is only used for Search.duckduckgo_provider, if you don't want to use it use Search._duckduckgo_provider instead.

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

aplustools is licensed under the GPL-3.0 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.

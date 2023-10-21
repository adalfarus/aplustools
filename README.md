[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![Build Status](https://github.com/Adalfarus/aplustools/workflows/python-publish.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: GPL-3.0](https://img.shields.io/github/license/Adafarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)

# aplustools

## Description

aplustools is a simple, user-friendly Python library for performing amazing tasks. It simplifies complex processes, allowing you to achieve more with less code. Developed with a focus on ease of use and efficiency, aplustools is the go-to solution for Python developers looking to enhance their projects.

## Features

- Easy to use
- Highly efficient
- Supports multiple platforms
- Regular updates and support
- Comprehensive documentation ( Not really lol )

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

Here's a few quick examples of how to use aplustools:

Search Engine usage
```python
from aplustools import Webtools

# Create an instance of Search
search = Webtools.Search()

# Call the `google_provider` with a parameter
result = search.google_provider("Hello, world!")

# Print the result
print(result)
```

Logger
```python
import aplustools.setdirtoex # Just the import is needed to set the current working directory to the main script of executable
import aplustools as apt

# Create an instance of Logger
logger = apt.Logs.Logger("my_logs_file.log", show_time=True, capture_print=False, overwrite_print=True, print_passthrough=False, print_log_to_stdout=True) # Shows the time in the logs (Like this [12:33:21]) and overwrites the normal sys.stdout

# Call the `monitor_stdout` method and pass the logger object
logger = apt.Logs.monitor_stdout(logger=logger) # Overwrite logger object here to close it later (You don't have to do this, if you keep the reference)

# Log something
logger.log("Hello, world!")

# Print something, it won't get captured or displayed
print("Hello, beautiful world!")

# Close the Logger object (returns sys-stdout to it's normal state)
logger.close()
```

OnlineImage
```python
from aplustools import Imagetools

# Download the Image
Imagetools.OnlineImage("someImage.url", True)

# Call the `google_provider` with a parameter
result = search.google_provider("Hello, world!")

# Print the result
print(result)
```

For more detailed usage and examples, check out our [documentation](https://example.com/docs).

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

aplustools is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

# aplustools
[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![Build Status](https://github.com/Adalfarus/aplustools/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: LGPL-2.1](https://img.shields.io/github/license/Adalfarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)

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
pip install aplustools --upgrade
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

# Print the results
print(results)

from aplustools.web.utils import WebPage

web_page = WebPage(next(iter(results)).get("url"))

if web_page.crawlable:
    print(web_page.page.content)
```

### Timer usage
````python
from aplustools.package.timid import TimidTimer
from datetime import timedelta
import time

# Setup your own timer class easily
mySpecialTimer = TimidTimer.setup_timer_func(time.time, to_nanosecond_multiplier=1e9)

timer = TimidTimer()

# Measure the average elapsed time over different iterations
for _ in range(4):
    timer.wait_ms(1000)
    timer.tock()
print("Average 1 second sleep extra delay: ", timer.average() - timedelta(seconds=1))

# Use multiple timers in one timer object using the index
with timer.enter(index=1):
    time.sleep(1)

# Use it for timed function execution
timer.start(index=1)  # The context manager automatically ends the timer, so we can reuse index 1 here
timer.shoot(interval=1, function=lambda: print("Shooting", timer.tock(index=1, return_datetime=True)), iterations=3)
print(timer.end())  # End the timer at index 0 that starts when the timer object gets created


def linear_time(n):
    # O(N) - Simple loop with linear complexity
    for _ in range(n):
        pass


def create_simple_input_generator():
    return ((tuple([n]), {}) for n in range(1, 100_001, 100))


# Measure the average time complexity of a function e.g. O(N)
print(timer.complexity(linear_time, create_simple_input_generator()))

# You can also show the curve
from matplotlib import pyplot

print(timer.complexity(linear_time, create_simple_input_generator(), matplotlib_pyplt=pyplot))


def complex_func(n, m, power=2):
    sum(i ** power for i in range(n)) + sum(j ** power for j in range(m))


def varying_func(n, multiplier=1):
    return sum(i * multiplier for i in range(n))


# Complex input generator with multiple arguments and keyword arguments
complex_input_generator = (
    (tuple([n, n // 2]), {'power': 2}) for n in range(1, 101)
)

# Complex input generator with varying keyword arguments
varying_input_generator = (
    (tuple([n]), {'multiplier': (n % 3 + 1)}) for n in range(1, 101)
)

print(f"Estimated Time Complexity for complex_func: {timer.complexity(complex_func, complex_input_generator, matplotlib_pyplt=pyplot)}")
print(f"Estimated Time Complexity for varying_func: {timer.complexity(varying_func, varying_input_generator, matplotlib_pyplt=pyplot)}")
````

### System
````python
from aplustools.io.environment import System


local_system = System.system()
print(type(local_system))  # This will output a specialized class

system_theme = local_system.theme
clipboard = local_system.get_clipboard()
local_system.send_notification("Title", "Message", (), ())
local_system.schedule_event("My event", script_path="./my_script.exe", event_time="startup")

print(f"{round(local_system.get_uptime(), 2)} minutes")
print(local_system.measure_network_speed())

for process in local_system.get_running_processes():
    print(process)
````

### Security
````python
from aplustools.security.passwords import GenerateWeakPasswords


input_sentence = input("Please input a sentence of your choosing: ")
password = GenerateWeakPasswords.generate_custom_sentence_based_password_v1(input_sentence, char_position="keep", 
                                                                            num_length=5, special_chars_length=2)
print(f"Your password is {password}")
````

(If you want to ensure that all dependencies are installed please run `upype import aplustools; aplustools.install_all_dependencies()`)
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
These can also be used in e.g. batch files like this
```batch
@echo off
set /p id=Enter ID: 
upype from aplustools.utils.security.passwords import GenerateWeakPasswords; print(GenerateWeakPasswords.generate_custom_sentence_based_password_v1("""%id%""", random_case=True, extra_char="""_""", char_position=0, num_length=5, special_chars_length=2))
pause

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
  - io.loggers
  - data.faker
  - utils.dummy
  - package.lazy_loader
- [`requests`]
  - data.github-updater-none
  - data.updaters
  - data.github-updater-cmd
- data.github-updater-gui - [`requests`, `PySide6`]
- data.imagetools - [`Pillow`, `aiohttp`, `requests`, `wand`]
- data.advanced_imagetools - [`opencv-python`, `aiohttp`, `wand`, `pillow_heif`]
- web.search, web.utils - [`requests`, `BeautifulSoup4`]
- security - [`cryptography`, `quantcrypt`]
- web.request - [`requests`, `aiohttp`]
- data.compressor - [`brotli`, `zstandard`, `py7zr`, `aplustools.security.crypto`]
- io.gui - [`PySide6`]
- io.environment - [`speedtest-cli`, `windows-toasts`]
- package.timid - [`numpy`]

Sub-Modules that may be removed in future updates due to being hard to support or simply unneeded.

- database (maybe unneeded and hard to support if more dbs are added -> new_database is being developed)
- loggers (maybe unneeded, default logging module is just really good)

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

aplustools is licensed under the LGPL-2.1 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.

[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![CI Test Status](https://github.com/Adalfarus/aplustools/actions/workflows/test-package.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: LGPL-2.1](https://img.shields.io/github/license/Adalfarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)

# aplustools

aplustools is a simple, user-friendly Python library for performing amazing tasks. It simplifies complex processes, allowing you to achieve more with less code. Developed with a focus on ease of use and efficiency, aplustools is the go-to solution for Python developers looking to enhance their projects.

## Compatibility
🟩 (Works perfectly); 🟨 (Untested); 🟧 (Some Issues); 🟥 (Unusable)

| OS                       | UX & README instructions | Tests | More Complex Functionalities |
|--------------------------|--------------------------|-------|------------------------------|
| Windows                  | 🟩                       | 🟩    | 🟩                           |
| MacOS                    | 🟨                       | 🟩    | 🟨                           |
| Linux (Ubuntu 22.04 LTS) | 🟩                       | 🟩    | 🟨                           |

## Features

- Easy to use for beginners, but not lacking for experts
- Pretty efficient
- Supports the three main platforms
- Regular updates and support
- Comprehensive documentation

## Installation

You can install aplustools via pip:

```sh
pip install aplustools[all] --upgrade
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

# Setting up your own timer
# Here we use the TimidTimer with the current time and a nanosecond multiplier
mySpecialTimer = TimidTimer.setup_timer_func(time.time, to_nanosecond_multiplier=1e9)

# Initialize the timer starting at 2.3 seconds
my_timer = mySpecialTimer(start_at=2.3)

# Perform some task
time.sleep(3.2)

# Print the elapsed time
print("This took:", my_timer.end())  # Expected output is approximately 1 second as we started at 2.3 seconds

# Advanced timer usage
timer = TimidTimer()

# Measure the average elapsed time over multiple iterations
for _ in range(4):
  timer.wait_ms_static(1000)  # Wait for 1 second
  timer.tock()  # Record the time
print("Average 1 second sleep extra delay:", timer.average() - timedelta(seconds=1))

# Using multiple timers within one timer object
with timer.enter(index=1):
  time.sleep(1)

# Using the timer for timed function execution
timer.start(index=1)  # Start the timer at index 1
timer.shoot(interval=1, function=lambda: print("Shooting", timer.tock(index=1, return_datetime=True)), iterations=3)
print(timer.end())  # End the timer at index 0 which started when the timer object was created

# Defining a function with linear time complexity
def linear_time(n):
  for _ in range(n):
    pass

# Create an input generator for the linear time function
def create_simple_input_generator():
  return ((tuple([n]), {}) for n in range(1, 100_001, 100))

# Measure the average time complexity of the function
print(timer.complexity(linear_time, create_simple_input_generator()))

# Plotting the time complexity curve
from matplotlib import pyplot
print(timer.complexity(linear_time, create_simple_input_generator(), matplotlib_pyplt=pyplot))

# Define a more complex function
def complex_func(n, m, power=2):
  return sum(i ** power for i in range(n)) + sum(j ** power for j in range(m))

# Define a varying function
def varying_func(n, multiplier=1):
  return sum(i * multiplier for i in range(n))

# Create input generators for the complex functions
complex_input_generator = ((tuple([n, n // 2]), {'power': 2}) for n in range(1, 101))
varying_input_generator = ((tuple([n]), {'multiplier': (n % 3 + 1)}) for n in range(1, 101))

# Measure and print the estimated time complexity for the complex functions
print(f"Estimated Time Complexity for complex_func: {timer.complexity(complex_func, complex_input_generator, matplotlib_pyplt=pyplot)}")
print(f"Estimated Time Complexity for varying_func: {timer.complexity(varying_func, varying_input_generator, matplotlib_pyplt=pyplot)}")
````

### System
````python
from aplustools.io.environment import get_system, BasicSystem


local_system = get_system()
print(type(local_system))  # This will output a specialized class

system_theme = local_system.get_system_theme()
clipboard = local_system.get_clipboard()
local_system.send_notification("Title", "Message", (), ())
local_system.schedule_event("My event", script_path="./my_script.exe", event_time="startup")

print(f"{round(BasicSystem.get_uptime(), 2)} minutes")
print(BasicSystem.measure_network_speed())

for process in BasicSystem.get_running_processes():
    print(process)
````

### PasswordGenerators
````python
from aplustools.security.passwords import QuickGeneratePasswords


input_sentence = input("Please input a sentence of your choosing: ")
password = QuickGeneratePasswords.generate_sentence_based_password(input_sentence)
print(f"Your password is {password}")


from aplustools.security.passwords import SecurePasswordGenerator

generator = SecurePasswordGenerator("strong")
secure_password = generator.generate_secure_password()
print(f"Secure password {secure_password}")
````
You can use the password generators like this in e.g. batch scripts:
```batch
@echo off
python -c "from aplustools.security.passwords import SecurePasswordGenerator; pw = SecurePasswordGenerator(""strong"").generate_secure_password(); print(f""{pw[""password""]}\n{pw[""extra_info""]} -> {pw[""worst_case""]}"")"
pause
```
or like this
````batch
@echo off
set /p id=Enter ID: 
python -c "from aplustools.security.passwords import SpecificPasswordGenerator; print(SpecificPasswordGenerator().generate_sentence_based_password_v3("""%id%""", random_case=True, extra_char="""_""", char_position=0, num_length=5, special_chars_length=2))"
pause
````

(If you have problems with the package please use `py -3.12 -m pip install aplustools[all] --upgrade --user`)
(Correct shortform for aplustools is apt, so please use ```import aplustools as apt``` for consistency)

### apt cli
Can currently run tests with ```aps tests run tests/ -minimal``` and show a basic help using ```aps help```.

For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and more
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

Sub-Modules that may be removed in future updates due to being hard to support or simply unneeded:
- database (maybe unneeded and hard to support if more dbs are added -> new_database is being developed)
- loggers (maybe unneeded, default logging module is just really good)

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

### Apt Build master

You can use the apt_build_master script for your os to make your like a lot easier.
It supports running tests, installing, building and much more as well as chain together as many commands as you like.

This example runs test, build the project and then installs it
````commandline
call .\apt_build_master.bat 234
````

````shell
sudo apt install python3-pip
sudo apt install python3-venv
chmod +x ./apt_build_master.sh
./apt_build_master.sh 234
````

## License

aplustools is licensed under the LGPL-2.1 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.

[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![CI Test Status](https://github.com/Adalfarus/aplustools/actions/workflows/test-package.yml/badge.svg)](https://github.com/Adalfarus/aplustools/actions)
[![License: LGPL-2.1](https://img.shields.io/github/license/Adalfarus/aplustools)](https://github.com/Adalfarus/aplustools/blob/main/LICENSE)

# aplustools2

aplustools2 is a simple, user-friendly Python library for performing amazing tasks. It simplifies complex processes, allowing you to achieve more with less code. Developed with a focus on ease of use and efficiency, aplustools is the go-to solution for Python developers looking to enhance their projects.

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

You can install aplustools2 via pip:

```sh
pip install aplustools[all]>=2.0.0.0 --upgrade
```

Or clone the repository and install manually:

```sh
git clone https://github.com/Adalfarus/aplustools.git
cd aplustools
python -m build
```

## Usage

Here are a few quick examples of how to use aplustools:

- Examples will be added in the full release.

(If you have problems with the package please use `py -3.12 -m pip install aplustools[all]>=2.0.0.0 --upgrade --user`)
(The standard shortform for aplustools is aps, so please use ```import aplustools as aps``` for consistency)

### aps cli
Can currently run tests with ```aps tests run tests/ -minimal``` and show a basic help using ```aps help```.

For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/aplustools/wiki).

## Naming convention, dependencies and library information
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

### Information
- Additional information will be added in the full release.

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/aplustools/blob/main/CONTRIBUTING.md) for more details on how you can contribute to aplustools.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

### Aps Build master

You can use the aps_build_master script for your os to make your like a lot easier.
It supports running tests, installing, building and much more as well as chaining together as many commands as you like.

This example runs test, build the project and then installs it
````commandline
call .\aps_build_master.bat 234
````

````shell
sudo apt install python3-pip
sudo apt install python3-venv
chmod +x ./aps_build_master.sh
./aps_build_master.sh 234
````

## License

aplustools is licensed under the LGPL-2.1 License - see the [LICENSE](https://github.com/adalfarus/aplustools/blob/main/LICENSE) file for details.

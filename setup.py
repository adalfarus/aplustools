from setuptools import find_packages, setup

# Read the content of the README.md file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='aplustools',
    packages=find_packages(include=['aplustools']),
    version='0.1.3.9', # Change to 0.1.4 if the duckduckgo search works aswell as DGGS
    description='A collection of helpful tools',
    author='Cariel Becker',
    license='GPL-3.0',
    install_requires=[
        'requests',
        'Pillow',
        'bs4',
        'datetime',
        'duckduckgo_search' # Get rid of
    ],
    # Include the long description from the README.md
    long_description=long_description,
    long_description_content_type="text/markdown",  # Indicate the content type (text/markdown, text/plain, text/x-rst)
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
    package_data={
        'aplustools': ['gitupdater.exe', 'gitupdater-cmd.exe', 'gitupdater-gui.exe'],
    }
)

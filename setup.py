from setuptools import find_packages, setup

setup(
    name='aplustools',
    packages=find_packages(include=['aplustools']),
    version='0.1.2', # Change to 0.1.3, when ImageTools are better and to 0.1.4 if the duckduckgo search works aswell as DGGS
    description='A collection of helpful tools',
    author='Cariel Becker',
    license='MIT',
    install_requires=[
        'numpy',
        'requests',
        'pyqt5',
        'Pillow',
        'requests',
        'duckduckgo_search' # Get rid of
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
    package_data={
        'aplustools': ['gitupdater.exe', 'gitupdater-cmd.exe', 'gitupdater-gui.exe'],
    }
)

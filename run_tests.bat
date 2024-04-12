@echo off
REM Make sure pytest is installed
py -m pip install pytest

REM Ensure test_data directory exists and is empty

set "DIR=test_data"

REM Check if directory exists
if exist "%DIR%" (
    echo Clearing directory %DIR%...
    rmdir /s /q "%DIR%"
)

echo Creating directory %DIR%...
mkdir "%DIR%"

REM Run tests

echo Running tests...

REM Using the pytest test runner and the
REM tests are in the 'tests' directory
pytest aplustools/tests

echo Tests completed.

if "%cmdcmdline%"=="" (
  echo Finished ...
)
pause

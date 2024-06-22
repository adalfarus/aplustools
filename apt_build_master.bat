@echo off
setlocal enabledelayedexpansion

REM Command line arguments processing
if not "%~1"=="" (
    set "choice=%1"
    goto process_choice_no_pause
)

REM Function to display the menu
:show_menu
cls
echo.
echo ==============================================================
echo                      AplusTools Main Menu
echo ==============================================================
echo 1.             Install pytest and run tests
echo 2.                 Clear dist directory
echo 3.                  Build the project
echo 4.           Install the newly built package
echo 5. Run all steps in order (1, 2, 3 ^& 4)
echo 0. Exit
echo ==============================================================
echo.
set /p choice="Enter your choice (0-5, or multiple choices): "

goto process_choice

REM Function to process the choice
:process_choice
setlocal enabledelayedexpansion
for /l %%i in (0,1,31) do (
    set "opt=!choice:~%%i,1!"
    if "!opt!" == "1" call :run_tests
    if "!opt!" == "2" call :clear
    if "!opt!" == "3" call :build_project
    if "!opt!" == "4" call :install_package
    if "!opt!" == "5" call :run_all
    if "!opt!" == "0" goto end
)
pause
goto end

REM Process choice without pause
:process_choice_no_pause
setlocal enabledelayedexpansion
for /l %%i in (0,1,31) do (
    set "opt=!choice:~%%i,1!"
    if "!opt!" == "1" call :run_tests
    if "!opt!" == "2" call :clear
    if "!opt!" == "3" call :build_project
    if "!opt!" == "4" call :install_package
    if "!opt!" == "5" call :run_all
    if "!opt!" == "0" goto end
)
goto end

REM Function to run tests
:run_tests
@echo off
REM Install pytest
py -m pip install pytest

REM Ensure test_data directory exists and is empty
set "DIR=test_data"
if exist "%DIR%" (
    echo Clearing directory %DIR%...
    rmdir /s /q "%DIR%"
)
echo Creating directory %DIR%...
mkdir "%DIR%"

REM Run tests
echo Running tests...
pytest src/aplustools/tests
echo Tests completed.
exit /b

REM Function to build the project
:build_project
@echo off
echo Building the project...
py -m build
echo Build completed.
exit /b

REM Function to clear dist directory and build
:clear
@echo off
echo Clearing dist directory...
del /Q ".\dist\*.*"
exit /b

REM Function to install the newly built package
:install_package
@echo off
for %%F in (dist\*.whl) do (
    py -m pip install "%%F" --force-reinstall
)
echo Package installation completed.
exit /b

REM Function to run all steps
:run_all
@echo off
call :run_tests
call :build_project
call :install_package
exit /b

:end
echo Exiting...
endlocal
exit /b

REM Command line arguments processing
if "%1" NEQ "" (
    set "choice=%1"
    goto process_choice
)

REM Show the menu by default
goto show_menu

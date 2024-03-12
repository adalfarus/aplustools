@echo off
del /Q ".\dist\*.*"
call ./build.bat
call ./install2.bat
if "%cmdcmdline%"=="" (
  echo Started directly
) else (
  echo Started from command line
)
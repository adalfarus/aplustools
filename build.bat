@echo off
py -m build

if "%cmdcmdline%"=="" (
  echo Finished ...
  pause
)

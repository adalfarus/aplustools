@echo off
for %%F in (dist\*.whl) do (
    py -m pip uninstall "%%F" -y
    py -m pip install "%%F"
)

if "%cmdcmdline%"=="" (
  echo Finished ...
  pause
)

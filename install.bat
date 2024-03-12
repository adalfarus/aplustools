@echo off
for %%F in (dist\*.whl) do (
    py -m pip install "%%F" --force-reinstall
)
if "%cmdcmdline%"=="" (
  echo Finished ...
  pause
)

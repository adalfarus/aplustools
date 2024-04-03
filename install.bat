@echo off
for %%F in (dist\*.whl) do (
    py -m pip install "%%F" --force-reinstall
)

REM https://superuser.com/questions/1301373/how-can-i-tell-whether-a-batch-file-was-run-from-a-command-window
if "%CMDCMDLINE:"=%" == "%COMSPEC% " (
  pause
) else if "%CMDCMDLINE%" == "cmd.exe" (
  pause
) else if "%CMDCMDLINE:"=%" == "%COMSPEC% /c %~dpf0 " (
  REM started in command window
) else (
  REM started from other batch file
)

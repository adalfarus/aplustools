@echo off
del /Q ".\dist\*.*"
call ./build.bat
call ./install2.bat

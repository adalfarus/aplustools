@echo off
sphinx-apidoc -o docs/source/ ./src/aplustools
sphinx-build -b markdown docs/source docs/build/markdown


@echo off
:: This batch file acts as a wrapper to run the main Python script.
:: It passes all command-line arguments to the script.

python "%~dp0\..\src\main.py" %*

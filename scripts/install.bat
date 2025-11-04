
@echo off

echo Adding the allsorted script directory to your user PATH...

:: Get the directory of the current script
set "SCRIPT_DIR=%~dp0"

:: Add the script directory to the user's PATH permanently
:: The following command reads the existing PATH, appends the new path, and saves it.
:: It avoids adding the path if it already exists.

for /f "skip=2 tokens=3,*" %%a in ('reg query HKCU\Environment /v PATH') do set "CURRENT_PATH=%%a%%b"

if "%%CURRENT_PATH:%SCRIPT_DIR%=%%" == "%CURRENT_PATH%" (
    echo Appending script directory to PATH.
    setx PATH "%CURRENT_PATH%;%SCRIPT_DIR%"
) else (
    echo Script directory is already in your PATH.
)

echo.
echo --- IMPORTANT ---
echo The 'allsorted' command will be available in NEW command prompts.
echo You must restart your terminal for the changes to take effect.
echo.
echo Installation complete.
pause

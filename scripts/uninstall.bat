
@echo off

echo Removing the allsorted script directory from your user PATH...

:: Get the directory of the current script, which needs to be removed from the PATH
set "SCRIPT_DIR_TO_REMOVE=%~dp0"
:: The path in the registry won't have a trailing backslash
set SCRIPT_DIR_TO_REMOVE=%SCRIPT_DIR_TO_REMOVE:~0,-1%

:: It is very complex to safely remove a variable from the PATH in a batch script.
:: The most reliable method is to inform the user to do it manually.


echo.
echo --- MANUAL UNINSTALLATION REQUIRED ---
echo To complete uninstallation, you need to manually remove the 'allsorted' directory from your PATH.

echo 1. Type 'Edit the system environment variables' into the Start Menu and open it.
echo 2. Click the 'Environment Variables...' button.
echo 3. In the top section ('User variables'), select the 'Path' variable and click 'Edit...'.
echo 4. Find the entry that ends with 'allsorted\scripts' and click 'Delete'.
echo 5. Click OK on all windows to save the changes.
echo.
echo This is the safest way to ensure your PATH is not corrupted.
echo.
echo After removing it from your PATH, you can safely delete the 'allsorted' project folder.
echo.
pause

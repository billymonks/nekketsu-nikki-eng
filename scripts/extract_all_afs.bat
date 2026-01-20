@echo off
REM Extract all AFS archives from extracted-disc folder
REM Requires AFSPacker.exe in tools folder

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "AFS_TOOL=%PROJECT_DIR%\tools\AFSPacker.exe"
set "INPUT_DIR=%PROJECT_DIR%\extracted-disc"
set "OUTPUT_DIR=%PROJECT_DIR%\extracted-afs"

echo ============================================
echo AFS Archive Batch Extractor
echo ============================================
echo.

if not exist "%AFS_TOOL%" (
    echo ERROR: AFSPacker.exe not found at %AFS_TOOL%
    echo Please download from: https://github.com/MaikelChan/AFSPacker
    pause
    exit /b 1
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo Extracting AFS archives from: %INPUT_DIR%
echo Output directory: %OUTPUT_DIR%
echo.

for %%f in ("%INPUT_DIR%\*.AFS") do (
    set "BASENAME=%%~nf"
    echo Extracting: %%~nxf
    "%AFS_TOOL%" -e "%%f" "%OUTPUT_DIR%\!BASENAME!"
    echo.
)

echo ============================================
echo Extraction complete!
echo ============================================
pause

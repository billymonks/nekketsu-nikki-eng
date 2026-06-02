@echo off
REM Quick rebuild script for testing translations

python .\replace_text.py

cd /d "%~dp0\.."

echo === Staging text patches for MGDATA repack ===
copy /y modified-afs-contents\MGDATA\00000062 modified-images\mgdata_62.bin >nul
copy /y modified-afs-contents\MGDATA\00000063 modified-images\mgdata_63.bin >nul

echo === Rebuilding MGDATA.AFS ===
tools\mgrepack_v0.9.0\mgrepack.exe repack -extract extracted-images -replacement modified-images -out modified-disc-files\MGDATA.AFS

echo.
echo === Rebuilding GDI ===
tools\buildgdi.exe -rebuild -gdi original-disc\disc.gdi -data modified-disc-files -output translated-disc

echo.
echo === Done! Test: translated-disc\disc.gdi ===

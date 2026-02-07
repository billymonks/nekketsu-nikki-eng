@echo off
REM Quick rebuild script for testing translations

python .\merge_batches.py
python .\replace_text.py

cd /d "%~dp0\.."

echo === Rebuilding MGDATA.AFS ===
tools\AFSPacker.exe -c modified-afs-contents\MGDATA modified-disc-files\MGDATA.AFS

echo.
echo === Rebuilding GDI ===
tools\buildgdi.exe -rebuild -gdi original-disc\disc.gdi -data modified-disc-files -output translated-disc

echo.
echo === Done! Test: translated-disc\disc.gdi ===

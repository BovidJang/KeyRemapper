@echo off
echo ========================================
echo   Key Remapper - Build Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.6+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)

echo [2/3] Building EXE...
echo.
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "KeyRemapper" ^
    --clean ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo ========================================
echo   EXE: dist\KeyRemapper.exe
echo ========================================
echo.
pause

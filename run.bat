@echo off
:: ============================================
:: run.bat — Easy launcher for the traffic system
:: Double-click this file or run from cmd
:: ============================================

title Hybrid Traffic System Launcher
color 0A

echo.
echo  =============================================
echo   HYBRID INTELLIGENT TRAFFIC SYSTEM
echo   ACO + PSO + Emergency Priority
echo  =============================================
echo.
echo  [1] Generate network (run FIRST time only)
echo  [2] Baseline simulation
echo  [3] Optimized simulation
echo  [4] Compare both (recommended)
echo  [5] Optimized - NO GUI (fast/headless)
echo  [6] Exit
echo.

set /p choice="  Enter choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo Running setup.py ...
    python setup.py
    pause
)

if "%choice%"=="2" (
    echo.
    echo Starting BASELINE simulation ...
    python main.py --mode baseline
    pause
)

if "%choice%"=="3" (
    echo.
    echo Starting OPTIMIZED simulation ...
    python main.py --mode optimized
    pause
)

if "%choice%"=="4" (
    echo.
    echo Starting COMPARISON run (baseline then optimized) ...
    python main.py --compare
    pause
)

if "%choice%"=="5" (
    echo.
    echo Starting OPTIMIZED (headless, no GUI) ...
    python main.py --mode optimized --no-gui
    pause
)

if "%choice%"=="6" exit

:: Keep window open if user double-clicked
pause
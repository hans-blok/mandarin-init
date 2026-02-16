@echo off
REM ==============================================================================
REM Fetch Prompts - Windows Wrapper (fetch.bat)
REM ==============================================================================
REM Wrapper voor scripts\fetch_prompts.py die prompt-bestanden ophaalt op basis van
REM value stream code en fase (bijv. aeo.01 of sfw.03) en ze kopieert naar
REM .github\prompts van de target workspace.
REM
REM Gebruik (enkel verplicht argument):
REM   fetch.bat <code.fase>
REM Voorbeelden:
REM   fetch.bat aeo.01
REM   fetch.bat sfw.03
REM ==============================================================================

set vsfase=%~1

if "%vsfase%"=="" (
    set /p "vsfase=Value stream.fase (bijv. aeo.01): "
)

REM Sta geen extra parameters toe
if not "%~2"=="" (
    echo [ERROR] Alleen het argument ^<code.fase^> is toegestaan
    echo Gebruik: fetch.bat aeo.01
    echo.
    pause
    exit /b 1
)

if "%vsfase%"=="" (
    echo [ERROR] Geen value stream.fase opgegeven
    echo Gebruik: fetch.bat aeo.01
    echo.
    pause
    exit /b 1
)

REM Zorg dat logs map bestaat
if not exist "logs" mkdir logs

REM Timestamp voor logbestand
title Fetch Prompts
for /f "delims=" %%i in ('powershell -Command "Get-Date -Format 'yyyyMMdd-HHmmss'"') do set timestamp=%%i
set logfile=logs\fetch-prompts-%timestamp%.log

echo [INFO] Fetch prompts gestart om %time%
echo [INFO] Value stream.fase: %vsfase%
echo [INFO] Log: %logfile%
echo.

python scripts\fetch_prompts.py %vsfase% > %logfile% 2>&1
set exit_code=%ERRORLEVEL%

type %logfile%

echo.
if %exit_code% equ 0 (
    echo [WRAPPER] Fetch prompts success
    echo [WRAPPER] Log: %logfile%
) else (
    echo [WRAPPER] Fetch prompts failed met exit code %exit_code%
    echo [WRAPPER] Check log: %logfile%
)

exit /b %exit_code%

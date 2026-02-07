@echo off
REM ==============================================================================
REM Fetch Agents - Windows Wrapper
REM ==============================================================================
REM
REM Wrapper voor fetch_mandarin_agents.py die agents ophaalt uit mandarin-agents
REM repository (inclusief .github directory) op basis van gepubliceerd manifest 
REM (agents-publicatie.json).
REM
REM Gebruik:
REM   fetch-agents.bat <value-stream>   - Fetch agents voor value stream
REM   fetch-agents.bat utility          - Fetch utility agents
REM   fetch-agents.bat kennispublicatie - Fetch kennispublicatie agents
REM   fetch-agents.bat --list           - Toon beschikbare value streams
REM
REM Output:
REM   - Console: Directe feedback over fetch proces
REM   - Terminal log: logs\fetch-agents-YYYYMMDD-HHMMSS.log (wrapper output)
REM   - Markdown log: logs\fetch-agents-YYYYMMDD-HHMMSS.md (script output)
REM
REM ==============================================================================

REM Check if argument provided (unless --list)
if "%~1"=="" (
    echo [ERROR] Value stream argument is required
    echo.
    echo Gebruik: fetch-agents.bat ^<value-stream^>
    echo.
    echo Voorbeelden:
    echo   fetch-agents.bat utility
    echo   fetch-agents.bat kennispublicatie
    echo   fetch-agents.bat --list
    echo.
    pause
    exit /b 1
)

REM Create logs directory if needed
if not exist "logs" mkdir logs

REM Generate timestamp for wrapper log
for /f "delims=" %%i in ('powershell -Command "Get-Date -Format 'yyyyMMdd-HHmmss'"') do set timestamp=%%i
set logfile=logs\fetch-agents-%timestamp%.log

echo [INFO] Fetch agents wrapper gestart om %time%
echo [INFO] Target value stream: %1
echo [INFO] Output log: %logfile%
echo.

REM Run script with all arguments, log to file and console
python scripts\fetch_mandarin_agents.py %* > %logfile% 2>&1
set exit_code=%ERRORLEVEL%

REM Show log content
type %logfile%

REM Report result
echo.
if %exit_code% equ 0 (
    echo [WRAPPER] Fetch completed successfully
    echo [WRAPPER] Log: %logfile%
) else (
    echo [WRAPPER] Fetch failed with exit code %exit_code%
    echo [WRAPPER] Check log for details: %logfile%
)

exit /b %exit_code%

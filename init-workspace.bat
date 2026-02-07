@echo off
REM ==============================================================================
REM Initialize Workspace
REM ==============================================================================
REM
REM Doel:
REM   Richt een nieuwe workspace in volgens de workspace doctrine.
REM   Fetcht canon en mandarin-agents, creeert folder structuur,
REM   installeert fetch_agents.py en fetch-agents.bat.
REM
REM Gebruik:
REM   init-workspace.bat <value-stream>
REM   init-workspace.bat kennispublicatie
REM
REM Output:
REM   - canon/ (governance en doctrine)
REM   - mandarin-agents/ (agent definities)
REM   - scripts/fetch__mandarin_agents.py
REM   - fetch-agents.bat
REM   - beleid-<workspace-name>.md (template uit mandarin-canon)
REM   - Basis folder structuur (.github/prompts, scripts/runners, etc.)
REM
REM Vereisten:
REM   - Python 3.9+
REM   - Git in PATH
REM   - Internet connectie
REM
REM Traceability:
REM   - Script: scripts/init-workspace.py
REM   - Doctrine: canon/governance/workspace-doctrine.md
REM
REM ==============================================================================

echo.
echo ========================================
echo  Workspace Initialisatie
echo ========================================
echo.

REM Controleer of Python beschikbaar is
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python niet gevonden. Installeer Python 3.9+ en probeer opnieuw.
    echo.
    pause
    exit /b 1
)

REM Controleer of Git beschikbaar is
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git niet gevonden. Installeer Git en zorg dat het in PATH staat.
    echo.
    pause
    exit /b 1
)

REM Value stream is optioneel
if "%~1"=="" (
    echo [INFO] Geen value stream opgegeven - basis setup wordt uitgevoerd
    echo.
)

REM Controleer of init-workspace.py bestaat
if not exist "init-workspace.py" (
    echo [ERROR] Script niet gevonden: init-workspace.py
    echo.
    echo Dit script moet worden uitgevoerd vanuit de workspace root,
    echo waar init-workspace.py bestaat.
    echo.
    pause
    exit /b 1
)

REM Voer initialisatie uit
if "%~1"=="" (
    echo [INFO] Start workspace initialisatie zonder value stream
) else (
    echo [INFO] Start workspace initialisatie voor value stream: %~1
)
echo.

python init-workspace.py %*

REM Controleer exit code
if errorlevel 1 (
    echo.
    echo [ERROR] Initialisatie mislukt. Zie output hierboven voor details.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Workspace initialisatie voltooid!
echo.
pause
exit /b 0

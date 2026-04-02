@echo off
chcp 65001 >nul

REM Se placer dans le dossier du script (indispensable pour les chemins relatifs)
cd /d "%~dp0"

echo ======================================
echo   SLAMM Finances MMA Saint-Lunaire
echo ======================================
echo.

REM Verifier Python 3
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python 3 n'est pas installe.
    echo Telechargez-le sur https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python %PYVER% detecte. OK.

REM Detecter le port disponible (5000 par defaut, 5001 en repli)
set PORT=5000
netstat -an 2>nul | find "LISTENING" | find ":5000 " >nul 2>&1
if not errorlevel 1 (
    echo Port 5000 occupe, utilisation du port 5001...
    set PORT=5001
)
echo Utilisation du port %PORT%.

REM Autoriser le port dans le pare-feu Windows
netsh advfirewall firewall add rule name="SLAMM Flask" dir=in action=allow protocol=TCP localport=%PORT% >nul 2>&1

REM Creer le venv si absent
if not exist ".venv\" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
    if errorlevel 1 (
        echo ERREUR : impossible de creer l'environnement virtuel.
        pause
        exit /b 1
    )
)

REM Installer les dependances via le Python du venv (sans activer le venv)
echo Installation des dependances...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip >nul 2>&1
.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ERREUR : impossible d'installer les dependances.
    pause
    exit /b 1
)

echo.
echo Demarrage de l'application SLAMM...
echo Acces : http://127.0.0.1:%PORT%
echo.

REM Lancer Flask directement avec le Python du venv
set FLASK_PORT=%PORT%
start "SLAMM Flask" .venv\Scripts\python.exe app.py

REM Attendre que Flask soit pret (3 secondes)
timeout /t 3 /nobreak >nul

REM Ouvrir le navigateur (127.0.0.1 plus fiable que localhost sur Windows)
start "" http://127.0.0.1:%PORT%

echo.
echo Application demarree sur http://127.0.0.1:%PORT%
echo Fermez cette fenetre pour arreter.
pause

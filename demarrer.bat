@echo off
chcp 65001 >nul
echo ======================================
echo   SLAMM ^— Finances MMA Saint-Lunaire
echo ======================================
echo.

REM Verifier Python 3
python --version >/dev/null 2>&1
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
netstat -an 2>/dev/null | find "LISTENING" | find ":5000 " >/dev/null 2>&1
if not errorlevel 1 (
    echo Port 5000 occupe, utilisation du port 5001...
    set PORT=5001
)
echo Utilisation du port %PORT%.

REM Autoriser le port dans le pare-feu Windows
netsh advfirewall firewall add rule name="SLAMM Flask" dir=in action=allow protocol=TCP localport=%PORT% >/dev/null 2>&1

REM Creer le venv si absent
if not exist ".venv\" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
)

REM Activer le venv
call .venv\Scripts\activate.bat

REM Installer les dependances
echo Installation des dependances...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo.
echo Demarrage de l'application SLAMM...
echo Acces : http://127.0.0.1:%PORT%
echo.

REM Lancer Flask avec le port selectionne
set FLASK_PORT=%PORT%
start "" python app.py

REM Attendre que Flask soit pret (3 secondes)
timeout /t 3 /nobreak >nul

REM Ouvrir le navigateur (127.0.0.1 plus fiable que localhost sur Windows)
start "" http://127.0.0.1:%PORT%

echo SLAMM — Application demarree sur le port %PORT%.
echo Fermez cette fenetre pour arreter.
pause

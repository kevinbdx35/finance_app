@echo off
chcp 65001 >nul
echo ======================================
echo   SLAMM ^— Finances MMA Saint-Lunaire
echo ======================================
echo.

REM Vérifier Python 3
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python 3 n'est pas installé.
    echo Téléchargez-le sur https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python %PYVER% détecté. OK.

REM Créer le venv si absent
if not exist ".venv\" (
    echo Création de l'environnement virtuel...
    python -m venv .venv
)

REM Activer le venv
call .venv\Scripts\activate.bat

REM Installer les dépendances
echo Installation des dépendances...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo.
echo Démarrage de l'application SLAMM...
echo Accès : http://localhost:5001
echo.

REM Lancer Flask en arrière-plan
start "" python app.py

REM Attendre 1.5s
timeout /t 2 /nobreak >nul

REM Ouvrir le navigateur
start "" http://localhost:5001

echo SLAMM — Application démarrée.
echo Fermez cette fenêtre pour arrêter.
pause

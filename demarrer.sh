#!/usr/bin/env bash
set -e

echo "======================================"
echo "  SLAMM — Finances MMA Saint-Lunaire"
echo "======================================"
echo ""

# Vérifier Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERREUR : Python 3 n'est pas installé."
    echo "Installez-le via : sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info.major, sys.version_info.minor)")
MAJOR=$(echo $PYTHON_VERSION | cut -d' ' -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d' ' -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
    echo "ERREUR : Python 3.8 ou supérieur requis (version détectée : $MAJOR.$MINOR)"
    exit 1
fi

echo "Python $MAJOR.$MINOR détecté. OK."

# Créer le venv si absent
if [ ! -d ".venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

# Activer le venv
source .venv/bin/activate

# Installer les dépendances
echo "Installation des dépendances..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "Démarrage de l'application SLAMM..."
echo "Accédez à : http://localhost:5001"
echo ""
echo "Fermez cette fenêtre (Ctrl+C) pour arrêter l'application."
echo ""

# Lancer Flask
export FLASK_APP=app.py
export FLASK_ENV=production
python3 app.py &
APP_PID=$!

# Attendre 1.5s puis ouvrir le navigateur
sleep 1.5
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5001 2>/dev/null &
elif command -v open &>/dev/null; then
    open http://localhost:5001 2>/dev/null &
fi

# Attendre la fin du processus Flask
wait $APP_PID

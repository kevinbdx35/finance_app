# SLAMM Finances

Application de comptabilité locale pour le club de MMA SLAMM — Saint-Lunaire (35).

> Fonctionne entièrement en local, sans internet, sans compte. Les données restent sur votre ordinateur.

---

## Installation — étape par étape

### Étape 1 — Télécharger l'application

Sur la page GitHub, cliquez sur le bouton vert **`< > Code`** puis **`Download ZIP`**.  
Extrayez le ZIP dans le dossier de votre choix (ex : `Documents/slamm-finances`).

### Étape 2 — Installer Python

Vérifiez d'abord si Python est déjà installé :

- **Windows** : ouvrez le menu Démarrer, tapez `cmd`, puis dans la fenêtre noire tapez `python --version`
- **Mac** : ouvrez le Launchpad → Terminal, tapez `python3 --version`
- **Linux** : ouvrez un terminal, tapez `python3 --version`

Si vous voyez `Python 3.x.x` → Python est installé, passez à l'étape 3.  
Sinon → téléchargez Python sur **https://www.python.org/downloads/** (bouton jaune "Download Python 3.x.x").

> ⚠ Windows : lors de l'installation, cochez **"Add Python to PATH"** avant de cliquer Installer.

### Étape 3 — Lancer l'application

**Windows** — double-cliquez sur le fichier `demarrer.bat`  
Une fenêtre noire s'ouvre, attendez quelques secondes, le navigateur s'ouvre automatiquement.

**Mac / Linux** — ouvrez un terminal dans le dossier du projet :
```bash
./demarrer.sh
```
> Si vous avez l'erreur "Permission denied" : tapez d'abord `chmod +x demarrer.sh` puis relancez.

### Étape 4 — Utiliser l'application

Ouvrez votre navigateur et allez sur : **http://localhost:5001**

Pour arrêter l'application : fermez la fenêtre noire (Windows) ou faites `Ctrl+C` dans le terminal.

---

## Relancer l'application

Même procédure : double-cliquez sur `demarrer.bat` (Windows) ou relancez `./demarrer.sh`.  
Vos données sont sauvegardées automatiquement, rien ne se perd.

---

## Données de test (optionnel)

Pour tester l'application avec des données fictives réalistes (transactions, budgets...) :

**Windows** — ouvrez `cmd` dans le dossier du projet, tapez :
```
.venv\Scripts\python generer_donnees_test.py
```

**Mac / Linux** :
```bash
.venv/bin/python generer_donnees_test.py
```

---

## Fonctionnalités

| Section | Description |
|---|---|
| Tableau de bord | Solde, graphiques entrées/sorties, alertes budget |
| Transactions | Ajout, modification, filtres, pièces jointes, export CSV/Excel |
| Documents | Stockage de contrats, licences, conventions |
| Budget | Suivi prévu vs réalisé par catégorie |
| Rapports PDF | Rapport mensuel, annuel, reçus individuels |
| Catégories | Personnalisables avec couleur |
| Paramètres | Sauvegarde et restauration de la base |

---

## Sauvegarde des données

Toutes les données sont dans le fichier `slamm_finances.db`.  
Pour sauvegarder : copiez ce fichier sur une clé USB ou dans votre cloud.  
Pour restaurer : **Paramètres → Restaurer** dans l'application.

---

## En cas de problème

| Problème | Solution |
|---|---|
| "Python n'est pas reconnu" | Réinstallez Python en cochant "Add to PATH" |
| La page ne s'ouvre pas | Ouvrez manuellement http://localhost:5001 |
| "Permission denied" (Mac/Linux) | Tapez `chmod +x demarrer.sh` dans le terminal |
| Port déjà utilisé | Changez `5001` en `5002` dans `app.py` (dernière ligne) |

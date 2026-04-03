# SLAMM Finances · v1.1.4

Application de comptabilité locale pour le club de MMA SLAMM — Saint-Lunaire (35).

> Fonctionne entièrement en local. Les données restent sur votre ordinateur et ne sont jamais envoyées nulle part.

---

## Installation — étape par étape

> L'installation via `git clone` est obligatoire pour bénéficier des **mises à jour automatiques**.

### Étape 1 — Installer Git

Vérifiez si Git est déjà installé en tapant `git --version` dans un terminal.

- **Windows** : téléchargez Git sur **https://git-scm.com/download/win** et installez-le (options par défaut)
- **Mac** : Git est inclus avec les outils développeur Xcode. Tapez `git --version`, macOS proposera l'installation si nécessaire
- **Linux** : `sudo apt install git` (Debian/Ubuntu) ou `sudo dnf install git` (Fedora)

### Étape 2 — Installer Python

Vérifiez d'abord si Python est déjà installé :

- **Windows** : ouvrez `cmd`, tapez `python --version`
- **Mac / Linux** : ouvrez un terminal, tapez `python3 --version`

Si vous voyez `Python 3.x.x` → passez à l'étape suivante.  
Sinon → téléchargez Python sur **https://www.python.org/downloads/**

> Windows : lors de l'installation, cochez **"Add Python to PATH"** avant de cliquer Installer.

### Étape 3 — Cloner le dépôt

Ouvrez un terminal dans le dossier où vous souhaitez installer l'application, puis tapez :

```bash
git clone https://github.com/kevinbdx35/finance_app.git
cd finance_app
```

### Étape 4 — Lancer l'application

**Windows** — double-cliquez sur le fichier `demarrer.bat`

La fenêtre noire effectue automatiquement :
- Vérification de Python
- Détection du port disponible (5000, ou 5001 si occupé)
- Autorisation du port dans le pare-feu Windows
- Création de l'environnement virtuel (première fois uniquement)
- Installation des dépendances
- Lancement de Flask + ouverture du navigateur

**Mac / Linux** :
```bash
./demarrer.sh
```
> Si vous avez l'erreur "Permission denied" : tapez d'abord `chmod +x demarrer.sh` puis relancez.

### Étape 5 — Ouvrir l'application

Le navigateur s'ouvre automatiquement sur **http://127.0.0.1:5000**

Si ce n'est pas le cas, ouvrez-le manuellement à cette adresse.

> La base de données est créée automatiquement au premier lancement — vous n'avez rien à faire.

Pour arrêter l'application : fermez la fenêtre noire (Windows) ou faites `Ctrl+C` dans le terminal.

---

## Mises à jour automatiques

Lorsqu'une nouvelle version est publiée sur GitHub, **un bandeau de notification apparaît automatiquement** dans l'interface (vérification silencieuse toutes les 10 minutes).

Cliquez sur **"Mettre à jour"** : l'application récupère les nouveaux fichiers et redémarre.  
**Vos données ne sont jamais touchées** — la base de données est exclue du processus de mise à jour.

La version courante est visible en bas du menu latéral et sur le tableau de bord.

---

## Relancer l'application

Même procédure : double-cliquez sur `demarrer.bat` (Windows) ou relancez `./demarrer.sh`.  
Vos données sont sauvegardées en permanence dans `slamm_finances.db`, rien ne se perd.

---

## Données de test (optionnel)

Pour tester l'application avec des données fictives réalistes (transactions, budgets, documents) :

**Windows** :
```
.venv\Scripts\python generer_donnees_test.py
```

**Mac / Linux** :
```bash
.venv/bin/python generer_donnees_test.py
```

> Ce script efface toutes les données existantes avant d'insérer les données de test.

---

## Fonctionnalités

| Section | Description |
|---|---|
| Tableau de bord | Solde, graphiques entrées/sorties sur 12 mois, alertes budget |
| Transactions | Ajout, modification, filtres avancés, pièces jointes, export CSV/Excel |
| Documents | Stockage de contrats, licences, conventions (PDF, images) |
| Budget | Suivi prévu vs réalisé par catégorie |
| Rapports PDF | Rapport mensuel, annuel, saison sportive (sep→août), reçus individuels |
| Catégories | Personnalisables avec couleur |
| Paramètres | Sauvegarde et restauration de la base de données |

---

## Sauvegarde des données

Toutes les données sont dans le fichier `slamm_finances.db`.

- **Sauvegarder** : copiez ce fichier sur une clé USB ou dans votre cloud
- **Restaurer** : **Paramètres → Restaurer** dans l'application, ou replacez simplement le fichier dans le dossier

---

## En cas de problème

| Problème | Solution |
|---|---|
| "Python n'est pas reconnu" | Réinstallez Python en cochant **"Add Python to PATH"** |
| "git n'est pas reconnu" | Installez Git (voir Étape 1) |
| La fenêtre se ferme immédiatement | Lancez `demarrer.bat` depuis l'explorateur (double-clic), pas depuis cmd |
| La page ne s'ouvre pas | Ouvrez manuellement **http://127.0.0.1:5000** (ou 5001) |
| "Permission denied" (Mac/Linux) | Tapez `chmod +x demarrer.sh` dans le terminal |
| Port déjà utilisé | `demarrer.bat` bascule automatiquement sur 5001 |
| Pare-feu bloque l'accès | `demarrer.bat` ajoute la règle automatiquement — sinon autorisez Python manuellement |
| Mise à jour échouée | Ouvrez un terminal dans le dossier et tapez `git pull` manuellement |

---

## Pour les développeurs

### Lancer les tests

```bash
.venv/bin/python tests.py
```

83 tests couvrant toutes les routes, le CRUD, les exports, la génération PDF, la sécurité des fichiers et les validations.

### Incrémenter la version manuellement

```bash
python scripts/bump_version.py patch   # 1.0.4 → 1.0.5 (défaut)
python scripts/bump_version.py minor   # 1.0.4 → 1.1.0
python scripts/bump_version.py major   # 1.0.4 → 2.0.0
```

La version est également incrémentée automatiquement à chaque `git commit` via le hook `pre-commit`.

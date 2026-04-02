"""
Génère des données de test réalistes pour SLAMM MMA Saint-Lunaire.
Lancement : python generer_donnees_test.py
"""
import sqlite3
import random
from datetime import date, timedelta
import os, sys

# S'assurer qu'on lance depuis le bon répertoire
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Initialiser la base
sys.path.insert(0, os.path.dirname(__file__))
import database as db
db.init_db()

conn = db.get_connection()
c = conn.cursor()

# Vider les données existantes avant d'insérer (évite les doublons)
print("Nettoyage des données existantes...")
# Supprimer les fichiers documents placeholders
existing_docs = conn.execute("SELECT file_path FROM documents").fetchall()
for row in existing_docs:
    fpath = os.path.join('documents', row[0])
    if os.path.exists(fpath):
        os.remove(fpath)
c.execute("DELETE FROM transactions")
c.execute("DELETE FROM budget")
c.execute("DELETE FROM documents")
conn.commit()

# Récupérer les catégories
categories = {r['name']: r['id'] for r in conn.execute("SELECT * FROM categories").fetchall()}

def rand_date(year, month):
    """Date aléatoire dans un mois donné."""
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    delta = (last - first).days
    return first + timedelta(days=random.randint(0, delta))

# ── Générer 12 mois de transactions ──────────────────────────────────────────

today = date.today()
start_year = today.year - 1
start_month = today.month

transactions = []

for i in range(12):
    m = (start_month + i - 1) % 12 + 1
    y = start_year + (start_month + i - 1) // 12

    # ENTRÉES
    # Cotisations adhérents (15-25 membres × 25€/mois)
    n_membres = random.randint(18, 28)
    for _ in range(n_membres):
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': f'Cotisation mensuelle — adhérent',
            'amount': 25.0,
            'type': 'income',
            'category': 'Cotisations adhérents',
            'notes': '',
        })

    # Licences FFMMA (en septembre surtout)
    if m in [9, 10, 11]:
        n_licences = random.randint(8, 15)
        for _ in range(n_licences):
            transactions.append({
                'date': rand_date(y, m).isoformat(),
                'label': 'Licence FFMMA annuelle',
                'amount': random.choice([45.0, 45.0, 45.0, 65.0]),  # junior/senior
                'type': 'income',
                'category': 'Licences FFMMA',
                'notes': '',
            })

    # Subventions (ponctuelles)
    if m == 3 and random.random() > 0.3:
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': 'Subvention Mairie de Saint-Lunaire',
            'amount': round(random.uniform(800, 1500), 2),
            'type': 'income',
            'category': 'Subventions',
            'notes': 'Subvention annuelle — activités sportives',
        })
    if m == 6 and random.random() > 0.5:
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': 'Subvention Conseil Départemental 35',
            'amount': round(random.uniform(500, 1200), 2),
            'type': 'income',
            'category': 'Subventions',
            'notes': 'Aide au développement des arts martiaux',
        })

    # SORTIES
    # Location salle (mensuelle)
    transactions.append({
        'date': rand_date(y, m).isoformat(),
        'label': 'Location salle polyvalente — Mairie',
        'amount': round(random.uniform(180, 220), 2),
        'type': 'expense',
        'category': 'Location salle',
        'notes': f'Créneaux MMA — {m:02d}/{y}',
    })

    # Assurance (annuelle en janvier)
    if m == 1:
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': 'Assurance annuelle MAIF — association sportive',
            'amount': round(random.uniform(320, 480), 2),
            'type': 'expense',
            'category': 'Assurances',
            'notes': 'Responsabilité civile + protection des dirigeants',
        })

    # Équipement (occasionnel)
    if random.random() > 0.4:
        equipements = [
            ('Gants de boxe MMA × 4 paires', 180, 280),
            ('Protège-tibia × 6', 90, 150),
            ('Casques de protection × 3', 120, 200),
            ('Tatami puzzle 20 dalles', 250, 450),
            ('Sac de frappe lourd 40kg', 150, 250),
            ('Coquilles de protection × 8', 80, 130),
            ('Shorts MMA × 10', 140, 220),
            ('Bandes de boxe × 20 paires', 60, 100),
            ('Gants de sparring × 6', 200, 320),
            ('Protège-dents moulés × 10', 70, 110),
        ]
        equip = random.choice(equipements)
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': f'Achat {equip[0]}',
            'amount': round(random.uniform(equip[1], equip[2]), 2),
            'type': 'expense',
            'category': 'Équipement',
            'notes': '',
        })

    # Compétitions (certains mois)
    if random.random() > 0.5:
        comps = [
            ('Inscriptions tournoi régional Bretagne MMA', 80, 180),
            ('Déplacement compétition — carburant + péages', 60, 120),
            ('Hébergement déplacement compétition', 140, 280),
            ('Frais d\'arbitrage tournoi FFMMA', 50, 100),
            ('Inscriptions championnats de Bretagne', 120, 200),
        ]
        comp = random.choice(comps)
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': comp[0],
            'amount': round(random.uniform(comp[1], comp[2]), 2),
            'type': 'expense',
            'category': 'Compétitions et déplacements',
            'notes': '',
        })

    # Communication (trimestrielle)
    if m in [1, 4, 7, 10]:
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': 'Création flyers + impression — saison MMA',
            'amount': round(random.uniform(80, 160), 2),
            'type': 'expense',
            'category': 'Communication',
            'notes': '',
        })

    # Charges diverses
    if random.random() > 0.5:
        charges = [
            ('Fournitures de bureau et administratives', 20, 60),
            ('Frais bancaires trimestriels', 15, 30),
            ('Cotisation fédération FFMMA', 50, 80),
            ('Abonnement logiciel gestion club', 10, 20),
            ('Trophées et médailles compétition interne', 80, 150),
        ]
        charge = random.choice(charges)
        transactions.append({
            'date': rand_date(y, m).isoformat(),
            'label': charge[0],
            'amount': round(random.uniform(charge[1], charge[2]), 2),
            'type': 'expense',
            'category': 'Charges diverses',
            'notes': '',
        })

# Insérer les transactions
print(f"Insertion de {len(transactions)} transactions...")
for tx in transactions:
    cat_id = categories.get(tx['category'])
    c.execute("""
        INSERT INTO transactions (date, label, amount, type, category_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tx['date'], tx['label'], tx['amount'], tx['type'], cat_id, tx['notes']))

# ── Budgets prévisionnels ─────────────────────────────────────────────────────

print("Insertion des budgets prévisionnels...")
for year in [today.year - 1, today.year]:
    budgets = [
        # (category_name, type, amount)
        ('Cotisations adhérents',        'income',  6000.0),
        ('Licences FFMMA',               'income',  2500.0),
        ('Subventions',                  'income',  2000.0),
        ('Licences FFMMA',               'expense', 1200.0),
        ('Équipement',                   'expense', 2500.0),
        ('Compétitions et déplacements', 'expense', 1500.0),
        ('Location salle',               'expense', 2400.0),
        ('Assurances',                   'expense',  450.0),
        ('Communication',                'expense',  600.0),
        ('Charges diverses',             'expense',  400.0),
    ]
    for name, typ, amount in budgets:
        cat_id = categories.get(name)
        if cat_id:
            c.execute("""
                INSERT INTO budget (year, category_id, type, amount)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(year, category_id, type) DO UPDATE SET amount=excluded.amount
            """, (year, cat_id, typ, amount))

# ── Documents fictifs ─────────────────────────────────────────────────────────

print("Insertion de documents fictifs...")
docs = [
    ('Statuts association SLAMM', '2019-06-15', 'Juridique',
     'Statuts constitutifs — Association loi 1901', 'statuts_slamm_2019.pdf'),
    ('Règlement intérieur 2024', '2024-01-10', 'Juridique',
     'Règlement intérieur mis à jour pour la saison 2024', 'reglement_interieur_2024.pdf'),
    ('Contrat assurance MAIF 2024', '2024-01-20', 'Financier',
     'Contrat responsabilité civile et protection des dirigeants', 'assurance_maif_2024.pdf'),
    ('Convention Mairie Saint-Lunaire', '2023-09-01', 'Admin',
     'Convention de mise à disposition de la salle polyvalente', 'convention_mairie_2023.pdf'),
    ('Affiliation FFMMA 2024-2025', '2024-09-05', 'Sportif',
     'Certificat d\'affiliation Fédération Française MMA', 'affiliation_ffmma_2024.pdf'),
    ('Récépissé déclaration préfecture', '2019-06-20', 'Juridique',
     'Récépissé officiel de déclaration en préfecture d\'Ille-et-Vilaine', 'recepisse_prefecture.pdf'),
    ('PV AG 2024', '2024-06-15', 'Admin',
     'Procès-verbal de l\'Assemblée Générale annuelle 2024', 'pv_ag_2024.pdf'),
    ('Subvention mairie — courrier 2024', '2024-03-10', 'Financier',
     'Courrier d\'attribution de la subvention municipale', 'subvention_mairie_2024.pdf'),
]

for name, dt, cat, notes, fname in docs:
    # Créer un fichier placeholder
    fpath = os.path.join('documents', fname)
    if not os.path.exists(fpath):
        with open(fpath, 'wb') as f:
            f.write(b'%PDF-1.4 placeholder document - ' + name.encode())
    c.execute("""
        INSERT OR IGNORE INTO documents (name, date, category, notes, file_path)
        VALUES (?, ?, ?, ?, ?)
    """, (name, dt, cat, notes, fname))

conn.commit()
conn.close()

print("\n✅ Données de test générées avec succès !")
print(f"   → {len(transactions)} transactions")
print(f"   → Budgets pour {today.year-1} et {today.year}")
print(f"   → {len(docs)} documents fictifs")
print("\nLancez l'application : .venv/bin/python app.py")
print("Puis ouvrez : http://localhost:5001")

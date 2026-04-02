import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'slamm_finances.db')

PREDEFINED_CATEGORIES = [
    ('Licences FFMMA',              'both',    '#C8102E'),
    ('Cotisations adhérents',        'income',  '#22C55E'),
    ('Subventions',                  'income',  '#3B82F6'),
    ('Équipement',                   'expense', '#F59E0B'),
    ('Compétitions et déplacements', 'expense', '#8B5CF6'),
    ('Location salle',               'expense', '#EC4899'),
    ('Assurances',                   'expense', '#06B6D4'),
    ('Communication',                'expense', '#F97316'),
    ('Charges diverses',             'expense', '#6B7280'),
]

DOCUMENT_CATEGORIES = ['Admin', 'Juridique', 'Financier', 'Sportif', 'Autre']


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL UNIQUE,
            type         TEXT NOT NULL DEFAULT 'both',
            color        TEXT NOT NULL DEFAULT '#888888',
            is_predefined INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            label           TEXT NOT NULL,
            amount          REAL NOT NULL,
            type            TEXT NOT NULL CHECK(type IN ('income','expense')),
            category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            notes           TEXT,
            attachment_path TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            year        INTEGER NOT NULL,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            type        TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount      REAL NOT NULL DEFAULT 0,
            UNIQUE(year, category_id, type)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            date        TEXT NOT NULL,
            category    TEXT NOT NULL DEFAULT 'Autre',
            notes       TEXT,
            file_path   TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Default settings
    defaults = {
        'association_name': 'SLAMM',
        'location': 'Saint-Lunaire, 35430',
        'currency': '€',
    }
    for key, value in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    # Predefined categories
    for name, typ, color in PREDEFINED_CATEGORIES:
        c.execute("""
            INSERT OR IGNORE INTO categories (name, type, color, is_predefined)
            VALUES (?, ?, ?, 1)
        """, (name, typ, color))

    conn.commit()
    conn.close()


# ── Settings ──────────────────────────────────────────────────────────────────

def get_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}


def update_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


# ── Categories ────────────────────────────────────────────────────────────────

def get_categories(type_filter=None):
    conn = get_connection()
    if type_filter:
        rows = conn.execute(
            "SELECT * FROM categories WHERE type = ? OR type = 'both' ORDER BY name",
            (type_filter,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category(cat_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_category(name, typ, color):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO categories (name, type, color) VALUES (?, ?, ?)", (name, typ, color))
    cat_id = c.lastrowid
    conn.commit()
    conn.close()
    return cat_id


def update_category(cat_id, name, typ, color):
    conn = get_connection()
    conn.execute(
        "UPDATE categories SET name=?, type=?, color=? WHERE id=?",
        (name, typ, color, cat_id)
    )
    conn.commit()
    conn.close()


def delete_category(cat_id):
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE category_id = ?", (cat_id,)
    ).fetchone()[0]
    if count > 0:
        conn.close()
        return False, f"Impossible : {count} transaction(s) utilisent cette catégorie."
    count_budget = conn.execute(
        "SELECT COUNT(*) FROM budget WHERE category_id = ?", (cat_id,)
    ).fetchone()[0]
    conn.execute("DELETE FROM budget WHERE category_id = ?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return True, "Catégorie supprimée."


# ── Transactions ──────────────────────────────────────────────────────────────

def get_transactions(filters=None, page=1, per_page=20):
    filters = filters or {}
    conn = get_connection()

    where = ["1=1"]
    params = []

    if filters.get('type'):
        where.append("t.type = ?")
        params.append(filters['type'])
    if filters.get('category_id'):
        where.append("t.category_id = ?")
        params.append(filters['category_id'])
    if filters.get('date_from'):
        where.append("t.date >= ?")
        params.append(filters['date_from'])
    if filters.get('date_to'):
        where.append("t.date <= ?")
        params.append(filters['date_to'])
    if filters.get('amount_min') is not None:
        where.append("t.amount >= ?")
        params.append(filters['amount_min'])
    if filters.get('amount_max') is not None:
        where.append("t.amount <= ?")
        params.append(filters['amount_max'])
    if filters.get('search'):
        where.append("(t.label LIKE ? OR t.notes LIKE ?)")
        s = f"%{filters['search']}%"
        params.extend([s, s])

    where_clause = " AND ".join(where)
    sort_col = filters.get('sort', 'date')
    sort_dir = 'DESC' if filters.get('dir', 'desc') == 'desc' else 'ASC'
    allowed_cols = {'date', 'label', 'amount', 'type'}
    if sort_col not in allowed_cols:
        sort_col = 'date'

    total = conn.execute(
        f"SELECT COUNT(*) FROM transactions t WHERE {where_clause}", params
    ).fetchone()[0]

    offset = (page - 1) * per_page
    rows = conn.execute(f"""
        SELECT t.*, c.name as category_name, c.color as category_color
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE {where_clause}
        ORDER BY t.{sort_col} {sort_dir}
        LIMIT ? OFFSET ?
    """, params + [per_page, offset]).fetchall()

    conn.close()
    return [dict(r) for r in rows], total


def get_transaction(tx_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT t.*, c.name as category_name, c.color as category_color
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = ?
    """, (tx_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_transaction(date, label, amount, typ, category_id, notes, attachment_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (date, label, amount, type, category_id, notes, attachment_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date, label, float(amount), typ, category_id or None, notes, attachment_path))
    tx_id = c.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def update_transaction(tx_id, date, label, amount, typ, category_id, notes, attachment_path):
    conn = get_connection()
    conn.execute("""
        UPDATE transactions
        SET date=?, label=?, amount=?, type=?, category_id=?, notes=?, attachment_path=?
        WHERE id=?
    """, (date, label, float(amount), typ, category_id or None, notes, attachment_path, tx_id))
    conn.commit()
    conn.close()


def delete_transaction(tx_id):
    conn = get_connection()
    row = conn.execute("SELECT attachment_path FROM transactions WHERE id=?", (tx_id,)).fetchone()
    conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return row['attachment_path'] if row else None


# ── Dashboard stats ───────────────────────────────────────────────────────────

def get_monthly_stats(year, month):
    conn = get_connection()
    prefix = f"{year:04d}-{month:02d}"
    income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND date LIKE ?",
        (f"{prefix}%",)
    ).fetchone()[0]
    expense = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND date LIKE ?",
        (f"{prefix}%",)
    ).fetchone()[0]
    conn.close()
    return float(income), float(expense)


def get_total_balance():
    conn = get_connection()
    income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income'"
    ).fetchone()[0]
    expense = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense'"
    ).fetchone()[0]
    conn.close()
    return float(income) - float(expense)


def get_last_transactions(n=5):
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*, c.name as category_name, c.color as category_color
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.date DESC, t.id DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_chart_data(months=12):
    """Returns last N months income/expense for bar chart."""
    from datetime import date
    today = date.today()
    results = []
    conn = get_connection()
    for i in range(months - 1, -1, -1):
        # Go back i months from today
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        prefix = f"{y:04d}-{m:02d}"
        income = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND date LIKE ?",
            (f"{prefix}%",)
        ).fetchone()[0]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND date LIKE ?",
            (f"{prefix}%",)
        ).fetchone()[0]
        results.append({
            'label': f"{m:02d}/{y}",
            'income': float(income),
            'expense': float(expense),
        })
    conn.close()
    return results


def get_category_donut_data(year, month):
    conn = get_connection()
    prefix = f"{year:04d}-{month:02d}"
    rows = conn.execute("""
        SELECT c.name, c.color, COALESCE(SUM(t.amount),0) as total
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.type='expense' AND t.date LIKE ?
        GROUP BY t.category_id
        ORDER BY total DESC
    """, (f"{prefix}%",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_last_update():
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(created_at) as last FROM transactions"
    ).fetchone()
    conn.close()
    return row['last'] if row and row['last'] else None


# ── Budget ────────────────────────────────────────────────────────────────────

def get_budget(year):
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.*, c.name as category_name, c.color as category_color, c.type as cat_type
        FROM budget b
        JOIN categories c ON b.category_id = c.id
        WHERE b.year = ?
        ORDER BY b.type, c.name
    """, (year,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_budget(year, category_id, typ, amount):
    conn = get_connection()
    conn.execute("""
        INSERT INTO budget (year, category_id, type, amount)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(year, category_id, type) DO UPDATE SET amount=excluded.amount
    """, (year, category_id, typ, float(amount)))
    conn.commit()
    conn.close()


def get_budget_realization(year):
    """Budget vs actual for a year."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            c.id as category_id,
            c.name as category_name,
            c.color as category_color,
            b.type,
            b.amount as budget_amount,
            COALESCE((
                SELECT SUM(t.amount)
                FROM transactions t
                WHERE t.category_id = c.id
                  AND t.type = b.type
                  AND strftime('%Y', t.date) = ?
            ), 0) as actual_amount
        FROM budget b
        JOIN categories c ON b.category_id = c.id
        WHERE b.year = ?
        ORDER BY b.type, c.name
    """, (str(year), year)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_budget_alerts(year, month):
    """Categories where actual >= budget."""
    conn = get_connection()
    prefix = f"{year:04d}-{month:02d}"
    rows = conn.execute("""
        SELECT c.name, b.amount as budget_amount,
               COALESCE(SUM(t.amount), 0) as actual_amount
        FROM budget b
        JOIN categories c ON b.category_id = c.id
        LEFT JOIN transactions t ON t.category_id = c.id
            AND t.type = b.type
            AND t.date LIKE ?
        WHERE b.year = ? AND b.type = 'expense'
        GROUP BY b.id
        HAVING actual_amount >= b.amount AND b.amount > 0
    """, (f"{prefix}%", year)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Documents ─────────────────────────────────────────────────────────────────

def get_documents(search=None, category=None):
    conn = get_connection()
    where = ["1=1"]
    params = []
    if search:
        where.append("(name LIKE ? OR notes LIKE ?)")
        s = f"%{search}%"
        params.extend([s, s])
    if category:
        where.append("category = ?")
        params.append(category)
    rows = conn.execute(
        f"SELECT * FROM documents WHERE {' AND '.join(where)} ORDER BY date DESC, id DESC",
        params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_document(name, date, category, notes, file_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO documents (name, date, category, notes, file_path) VALUES (?,?,?,?,?)",
        (name, date, category, notes, file_path)
    )
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def delete_document(doc_id):
    conn = get_connection()
    row = conn.execute("SELECT file_path FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return row['file_path'] if row else None


# ── Reports helpers ───────────────────────────────────────────────────────────

def get_transactions_for_report(year, month=None):
    conn = get_connection()
    if month:
        prefix = f"{year:04d}-{month:02d}%"
        rows = conn.execute("""
            SELECT t.*, c.name as category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.date LIKE ?
            ORDER BY t.date, t.id
        """, (prefix,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT t.*, c.name as category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE strftime('%Y', t.date) = ?
            ORDER BY t.date, t.id
        """, (str(year),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_summary(year, month=None):
    conn = get_connection()
    if month:
        date_filter = f"AND t.date LIKE '{year:04d}-{month:02d}%'"
    else:
        date_filter = f"AND strftime('%Y', t.date) = '{year}'"
    rows = conn.execute(f"""
        SELECT c.name as category_name, c.color, t.type,
               COALESCE(SUM(t.amount), 0) as total
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE 1=1 {date_filter}
        GROUP BY t.category_id, t.type
        ORDER BY t.type, total DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

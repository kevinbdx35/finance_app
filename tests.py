"""
Suite de tests de régression — SLAMM Finances
Lancement : python tests.py  (ou python -m pytest tests.py -v)
"""
import io
import os
import sys
import tempfile
import unittest

# Pointer sur la base de test en mémoire avant tout import
os.environ['SLAMM_TEST'] = '1'

# Patch DB_PATH avant l'import de database
import database as db

_TMP_DB = None


def setUpModule():
    global _TMP_DB
    _TMP_DB = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    _TMP_DB.close()
    db.DB_PATH = _TMP_DB.name
    db.init_db()


def tearDownModule():
    if _TMP_DB:
        os.unlink(_TMP_DB.name)


# ── Import app après avoir patché DB_PATH ─────────────────────────────────────
import app as application

application.app.config['TESTING'] = True
application.app.config['WTF_CSRF_ENABLED'] = False


def get_client():
    return application.app.test_client()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_cat_counter = 0


def _create_category(name='Test Cat', typ='both', color='#123456'):
    """Crée une catégorie avec un nom unique pour éviter les conflits UNIQUE."""
    global _cat_counter
    _cat_counter += 1
    unique_name = f"{name}_{_cat_counter}"
    return db.create_category(unique_name, typ, color)


def _create_transaction(label='Test TX', amount=100.0, typ='income',
                        cat_id=None, date='2025-01-15'):
    return db.create_transaction(
        date=date, label=label, amount=amount, typ=typ,
        category_id=cat_id, notes='', attachment_path=None,
    )


def _create_document(name='Doc test', file_path='test.pdf'):
    return db.create_document(
        name=name, date='2025-01-01', category='Admin',
        notes='', file_path=file_path,
    )


# =============================================================================
# 1. Routes HTTP — codes de réponse
# =============================================================================

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_dashboard(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'SLAMM', r.data)

    def test_transactions_page(self):
        r = self.client.get('/transactions')
        self.assertEqual(r.status_code, 200)

    def test_documents_page(self):
        r = self.client.get('/documents')
        self.assertEqual(r.status_code, 200)

    def test_budget_page(self):
        r = self.client.get('/budget')
        self.assertEqual(r.status_code, 200)

    def test_rapports_page(self):
        r = self.client.get('/rapports')
        self.assertEqual(r.status_code, 200)

    def test_categories_page(self):
        r = self.client.get('/categories')
        self.assertEqual(r.status_code, 200)

    def test_parametres_page(self):
        r = self.client.get('/parametres')
        self.assertEqual(r.status_code, 200)

    def test_404(self):
        r = self.client.get('/route-inexistante')
        self.assertEqual(r.status_code, 404)
        self.assertIn(b'404', r.data)

    def test_version_in_dashboard(self):
        r = self.client.get('/')
        self.assertIn(b'v1.', r.data)


# =============================================================================
# 2. CRUD Transactions
# =============================================================================

class TestTransactionCRUD(unittest.TestCase):

    def setUp(self):
        self.client = get_client()
        self.cat_id = _create_category('CatTx', 'both', '#AABBCC')

    def test_create_transaction(self):
        tx_id = _create_transaction('Cotisation', 25.0, 'income', self.cat_id)
        self.assertIsNotNone(tx_id)
        tx = db.get_transaction(tx_id)
        self.assertEqual(tx['label'], 'Cotisation')
        self.assertAlmostEqual(tx['amount'], 25.0)
        self.assertEqual(tx['type'], 'income')

    def test_update_transaction(self):
        tx_id = _create_transaction('Ancien label', 50.0, 'expense', self.cat_id)
        db.update_transaction(
            tx_id=tx_id, date='2025-02-01', label='Nouveau label',
            amount=75.0, typ='expense', category_id=self.cat_id,
            notes='note', attachment_path=None,
        )
        tx = db.get_transaction(tx_id)
        self.assertEqual(tx['label'], 'Nouveau label')
        self.assertAlmostEqual(tx['amount'], 75.0)

    def test_delete_transaction(self):
        tx_id = _create_transaction()
        db.delete_transaction(tx_id)
        self.assertIsNone(db.get_transaction(tx_id))

    def test_get_transactions_filter_type(self):
        _create_transaction('Entrée', 100.0, 'income', self.cat_id, '2025-03-01')
        _create_transaction('Sortie', 50.0, 'expense', self.cat_id, '2025-03-02')
        txs, total = db.get_transactions({'type': 'income'})
        for tx in txs:
            self.assertEqual(tx['type'], 'income')

    def test_get_transactions_filter_search(self):
        _create_transaction('Loyer Salle XYZ', 200.0, 'expense', self.cat_id)
        txs, _ = db.get_transactions({'search': 'XYZ'})
        self.assertTrue(any('XYZ' in tx['label'] for tx in txs))

    def test_add_transaction_via_http(self):
        count_before = db.get_transactions()[1]
        r = self.client.post('/transactions/add', data={
            'date': '2025-04-01',
            'label': 'TX via HTTP',
            'amount': '42.50',
            'type': 'income',
            'category_id': str(self.cat_id),
            'notes': '',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        count_after = db.get_transactions()[1]
        self.assertEqual(count_after, count_before + 1)

    def test_delete_transaction_via_http(self):
        tx_id = _create_transaction('A supprimer HTTP')
        r = self.client.post(f'/transactions/{tx_id}/delete',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(db.get_transaction(tx_id))

    def test_edit_transaction_via_http(self):
        tx_id = _create_transaction('Original')
        r = self.client.post(f'/transactions/{tx_id}/edit', data={
            'date': '2025-05-01',
            'label': 'Modifié',
            'amount': '99.99',
            'type': 'income',
            'category_id': str(self.cat_id),
            'notes': '',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        tx = db.get_transaction(tx_id)
        self.assertEqual(tx['label'], 'Modifié')

    def test_invalid_transaction_404(self):
        r = self.client.post('/transactions/999999/edit', data={
            'date': '2025-01-01', 'label': 'x', 'amount': '1', 'type': 'income',
        })
        self.assertEqual(r.status_code, 404)


# =============================================================================
# 3. CRUD Catégories
# =============================================================================

class TestCategoryCRUD(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_create_category(self):
        cat_id = _create_category('Nouvelle Cat', 'expense', '#FF0000')
        cat = db.get_category(cat_id)
        self.assertIsNotNone(cat)
        self.assertIn('Nouvelle Cat', cat['name'])

    def test_update_category(self):
        cat_id = _create_category('Cat modif', 'both', '#000000')
        db.update_category(cat_id, f'Cat renommée {cat_id}', 'income', '#FFFFFF')
        cat = db.get_category(cat_id)
        self.assertIn('Cat renommée', cat['name'])
        self.assertEqual(cat['type'], 'income')

    def test_delete_category_unused(self):
        cat_id = _create_category('Cat supprimable', 'both', '#AAAAAA')
        ok, msg = db.delete_category(cat_id)
        self.assertTrue(ok)
        self.assertIsNone(db.get_category(cat_id))

    def test_delete_category_in_use(self):
        cat_id = _create_category('Cat en usage', 'both', '#BBBBBB')
        _create_transaction('TX lié', 10.0, 'income', cat_id)
        ok, msg = db.delete_category(cat_id)
        self.assertFalse(ok)
        # Category still exists
        self.assertIsNotNone(db.get_category(cat_id))

    def test_add_category_via_http(self):
        import uuid
        unique_name = f'CatHTTP_{uuid.uuid4().hex[:6]}'
        r = self.client.post('/categories/add', data={
            'name': unique_name,
            'type': 'both',
            'color': '#123456',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        cats = db.get_categories()
        self.assertTrue(any(c['name'] == unique_name for c in cats))

    def test_delete_category_via_http(self):
        cat_id = _create_category('CatDeleteHTTP', 'both', '#654321')
        r = self.client.post(f'/categories/{cat_id}/delete',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(db.get_category(cat_id))

    def test_get_categories_usage(self):
        cat_id = db.create_category('CatUsage', 'both', '#ABCDEF')
        _create_transaction('T1', 10.0, 'income', cat_id)
        _create_transaction('T2', 20.0, 'expense', cat_id)
        usage = db.get_categories_usage()
        self.assertGreaterEqual(usage.get(cat_id, 0), 2)


# =============================================================================
# 4. CRUD Documents
# =============================================================================

class TestDocumentCRUD(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_create_document(self):
        doc_id = db.create_document('Mon doc', '2025-01-01', 'Admin', 'notes', 'file.pdf')
        doc = db.get_document(doc_id)
        self.assertIsNotNone(doc)
        self.assertEqual(doc['name'], 'Mon doc')

    def test_update_document(self):
        doc_id = db.create_document('Ancien', '2025-01-01', 'Admin', '', 'old.pdf')
        db.update_document(doc_id, 'Nouveau', '2025-06-01', 'Juridique', 'notes mises à jour')
        doc = db.get_document(doc_id)
        self.assertEqual(doc['name'], 'Nouveau')
        self.assertEqual(doc['category'], 'Juridique')

    def test_delete_document(self):
        doc_id = db.create_document('À supprimer', '2025-01-01', 'Admin', '', 'del.pdf')
        db.delete_document(doc_id)
        self.assertIsNone(db.get_document(doc_id))

    def test_get_documents_search(self):
        db.create_document('Contrat MAIF 2024', '2025-01-01', 'Financier', '', 'maif.pdf')
        docs = db.get_documents(search='MAIF')
        self.assertTrue(any('MAIF' in d['name'] for d in docs))

    def test_get_documents_category_filter(self):
        db.create_document('Statuts', '2025-01-01', 'Juridique', '', 'statuts.pdf')
        db.create_document('Facture', '2025-01-02', 'Financier', '', 'facture.pdf')
        docs = db.get_documents(category='Juridique')
        for d in docs:
            self.assertEqual(d['category'], 'Juridique')

    def test_edit_document_via_http(self):
        doc_id = db.create_document('HTTP doc', '2025-01-01', 'Admin', '', 'http.pdf')
        r = self.client.post(f'/documents/{doc_id}/edit', data={
            'name': 'HTTP doc modifié',
            'date': '2025-03-01',
            'category': 'Juridique',
            'notes': 'mis à jour',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        doc = db.get_document(doc_id)
        self.assertEqual(doc['name'], 'HTTP doc modifié')

    def test_delete_document_via_http(self):
        doc_id = db.create_document('Del HTTP', '2025-01-01', 'Admin', '', 'delhttp.pdf')
        r = self.client.post(f'/documents/{doc_id}/delete',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(db.get_document(doc_id))

    def test_download_missing_document_404(self):
        r = self.client.get('/documents/999999/download')
        self.assertEqual(r.status_code, 404)


# =============================================================================
# 5. Budget
# =============================================================================

class TestBudget(unittest.TestCase):

    def setUp(self):
        self.client = get_client()
        self.cat_id = _create_category('BudgetCat', 'expense', '#556677')

    def test_save_and_get_budget(self):
        db.save_budget(2025, self.cat_id, 'expense', 1000.0)
        rows = db.get_budget(2025)
        self.assertTrue(any(
            r['category_id'] == self.cat_id and r['amount'] == 1000.0
            for r in rows
        ))

    def test_budget_upsert(self):
        db.save_budget(2025, self.cat_id, 'expense', 500.0)
        db.save_budget(2025, self.cat_id, 'expense', 800.0)
        rows = db.get_budget(2025)
        match = [r for r in rows if r['category_id'] == self.cat_id]
        self.assertEqual(match[-1]['amount'], 800.0)

    def test_budget_realization(self):
        db.save_budget(2025, self.cat_id, 'expense', 300.0)
        _create_transaction('Dépense', 120.0, 'expense', self.cat_id, '2025-06-10')
        rows = db.get_budget_realization(2025)
        match = [r for r in rows if r['category_id'] == self.cat_id]
        if match:
            self.assertAlmostEqual(match[0]['budget_amount'], 300.0)
            self.assertGreaterEqual(match[0]['actual_amount'], 120.0)

    def test_save_budget_via_http(self):
        r = self.client.post('/budget/save', data={
            'year': '2025',
            f'budget_{self.cat_id}_expense': '1200',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)


# =============================================================================
# 6. Exports CSV / Excel
# =============================================================================

class TestExports(unittest.TestCase):

    def setUp(self):
        self.client = get_client()
        cat_id = _create_category('ExportCat', 'both', '#998877')
        _create_transaction('Export TX 1', 100.0, 'income', cat_id, '2025-07-01')
        _create_transaction('Export TX 2', 50.0, 'expense', cat_id, '2025-07-02')

    def test_export_csv(self):
        r = self.client.get('/transactions/export/csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r.content_type)
        # Vérifie le BOM UTF-8 et les en-têtes
        content = r.data.decode('utf-8-sig')
        self.assertIn('Date', content)
        self.assertIn('Libellé', content)

    def test_export_csv_content(self):
        r = self.client.get('/transactions/export/csv')
        content = r.data.decode('utf-8-sig')
        self.assertIn('Export TX 1', content)
        self.assertIn('Export TX 2', content)

    def test_export_excel(self):
        r = self.client.get('/transactions/export/excel')
        self.assertEqual(r.status_code, 200)
        self.assertIn(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            r.content_type,
        )
        # Vérifie que c'est bien un fichier XLSX (magic bytes ZIP)
        self.assertTrue(r.data[:2] == b'PK')

    def test_export_csv_filter_type(self):
        r = self.client.get('/transactions/export/csv?type=income')
        content = r.data.decode('utf-8-sig')
        lines = [l for l in content.splitlines() if l.strip() and 'Date' not in l]
        for line in lines:
            if line.strip():
                self.assertIn('Entrée', line)


# =============================================================================
# 7. Génération PDF
# =============================================================================

class TestPDF(unittest.TestCase):

    def setUp(self):
        self.client = get_client()
        cat_id = _create_category('PDFCat', 'both', '#112233')
        _create_transaction('PDF TX', 75.0, 'expense', cat_id, '2025-08-15')

    def test_monthly_report(self):
        r = self.client.post('/rapports/monthly', data={
            'year': '2025', 'month': '8',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content_type, 'application/pdf')
        self.assertTrue(r.data.startswith(b'%PDF'))

    def test_annual_report(self):
        r = self.client.post('/rapports/annual', data={'year': '2025'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content_type, 'application/pdf')
        self.assertTrue(r.data.startswith(b'%PDF'))

    def test_receipt(self):
        cat_id = _create_category('ReceiptCat', 'both', '#AABBCC')
        tx_id = _create_transaction('Reçu test', 30.0, 'expense', cat_id, '2025-09-01')
        r = self.client.get(f'/rapports/receipt/{tx_id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content_type, 'application/pdf')
        self.assertTrue(r.data.startswith(b'%PDF'))

    def test_receipt_not_found(self):
        r = self.client.get('/rapports/receipt/999999')
        self.assertEqual(r.status_code, 404)


# =============================================================================
# 8. Fonctions base de données
# =============================================================================

class TestDatabase(unittest.TestCase):

    def test_get_total_balance(self):
        # On ne teste pas la valeur absolue (dépend des autres tests),
        # juste que la fonction retourne un float sans erreur.
        balance = db.get_total_balance()
        self.assertIsInstance(balance, float)

    def test_get_monthly_stats(self):
        cat_id = _create_category('StatCat', 'both', '#FEDCBA')
        _create_transaction('Income stat', 200.0, 'income', cat_id, '2025-11-10')
        _create_transaction('Expense stat', 80.0, 'expense', cat_id, '2025-11-15')
        income, expense = db.get_monthly_stats(2025, 11)
        self.assertGreaterEqual(income, 200.0)
        self.assertGreaterEqual(expense, 80.0)

    def test_get_monthly_chart_data(self):
        data = db.get_monthly_chart_data(6)
        self.assertEqual(len(data), 6)
        for entry in data:
            self.assertIn('label', entry)
            self.assertIn('income', entry)
            self.assertIn('expense', entry)

    def test_get_last_transactions(self):
        cat_id = _create_category('LastCat', 'both', '#ABCABC')
        for i in range(3):
            _create_transaction(f'Last TX {i}', 10.0 * (i + 1), 'income', cat_id)
        txs = db.get_last_transactions(3)
        self.assertLessEqual(len(txs), 3)

    def test_get_settings_defaults(self):
        settings = db.get_settings()
        self.assertIn('currency', settings)
        self.assertIn('association_name', settings)

    def test_update_setting(self):
        db.update_setting('currency', '$')
        settings = db.get_settings()
        self.assertEqual(settings['currency'], '$')
        # Remettre en place
        db.update_setting('currency', '€')

    def test_get_categories(self):
        cats = db.get_categories()
        self.assertIsInstance(cats, list)
        self.assertGreater(len(cats), 0)

    def test_get_categories_type_filter(self):
        db.create_category('OnlyExpense', 'expense', '#112233')
        cats = db.get_categories(type_filter='income')
        for c in cats:
            self.assertIn(c['type'], ('income', 'both'))

    def test_get_category_donut_data(self):
        data = db.get_category_donut_data(2025, 7)
        # Retourne une liste (peut être vide si aucune dépense ce mois)
        self.assertIsInstance(data, list)

    def test_get_transactions_pagination(self):
        cat_id = _create_category('PageCat', 'both', '#FEDCBA')
        for i in range(5):
            _create_transaction(f'Page TX {i}', 5.0, 'income', cat_id)
        _, total = db.get_transactions({}, page=1, per_page=2)
        txs_p1, _ = db.get_transactions({}, page=1, per_page=2)
        txs_p2, _ = db.get_transactions({}, page=2, per_page=2)
        self.assertLessEqual(len(txs_p1), 2)
        self.assertLessEqual(len(txs_p2), 2)

    def test_get_transactions_sort(self):
        cat_id = _create_category('SortCat', 'both', '#123123')
        _create_transaction('Sort A', 10.0, 'income', cat_id, '2025-01-01')
        _create_transaction('Sort B', 20.0, 'income', cat_id, '2025-06-01')
        txs_asc, _ = db.get_transactions({'sort': 'date', 'dir': 'asc'})
        txs_desc, _ = db.get_transactions({'sort': 'date', 'dir': 'desc'})
        if len(txs_asc) >= 2 and len(txs_desc) >= 2:
            self.assertLessEqual(txs_asc[0]['date'], txs_asc[-1]['date'])
            self.assertGreaterEqual(txs_desc[0]['date'], txs_desc[-1]['date'])


# =============================================================================
# 9. Erreurs personnalisées
# =============================================================================

class TestErrors(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_404_page(self):
        r = self.client.get('/page-qui-nexiste-pas')
        self.assertEqual(r.status_code, 404)
        self.assertIn(b'404', r.data)

    def test_404_transaction(self):
        r = self.client.get('/transactions/999999/attachment')
        self.assertEqual(r.status_code, 404)

    def test_404_document_download(self):
        r = self.client.get('/documents/999999/download')
        self.assertEqual(r.status_code, 404)


# =============================================================================
# 10. API JSON
# =============================================================================

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_api_transaction_found(self):
        cat_id = _create_category('APICat', 'both', '#111222')
        tx_id = _create_transaction('API TX', 55.0, 'income', cat_id)
        r = self.client.get(f'/api/transaction/{tx_id}')
        self.assertEqual(r.status_code, 200)
        import json
        data = json.loads(r.data)
        self.assertEqual(data['id'], tx_id)
        self.assertAlmostEqual(data['amount'], 55.0)

    def test_api_transaction_not_found(self):
        r = self.client.get('/api/transaction/999999')
        self.assertEqual(r.status_code, 404)

    def test_api_document_found(self):
        doc_id = db.create_document('API Doc', '2025-01-01', 'Admin', '', 'api.pdf')
        r = self.client.get(f'/api/document/{doc_id}')
        self.assertEqual(r.status_code, 200)
        import json
        data = json.loads(r.data)
        self.assertEqual(data['id'], doc_id)

    def test_api_document_not_found(self):
        r = self.client.get('/api/document/999999')
        self.assertEqual(r.status_code, 404)


# =============================================================================
# 11. Sécurité — validation fichiers
# =============================================================================

class TestFileSecurity(unittest.TestCase):

    def test_valid_pdf_magic(self):
        fake_pdf = io.BytesIO(b'%PDF-1.4 content here')
        self.assertTrue(application.valid_file_content(fake_pdf))

    def test_valid_png_magic(self):
        fake_png = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        self.assertTrue(application.valid_file_content(fake_png))

    def test_valid_jpg_magic(self):
        fake_jpg = io.BytesIO(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        self.assertTrue(application.valid_file_content(fake_jpg))

    def test_invalid_file_content(self):
        fake_txt = io.BytesIO(b'Hello world this is not a valid file type')
        self.assertFalse(application.valid_file_content(fake_txt))

    def test_allowed_file_extensions(self):
        self.assertTrue(application.allowed_file('document.pdf'))
        self.assertTrue(application.allowed_file('photo.jpg'))
        self.assertTrue(application.allowed_file('photo.jpeg'))
        self.assertTrue(application.allowed_file('image.png'))
        self.assertFalse(application.allowed_file('script.exe'))
        self.assertFalse(application.allowed_file('script.py'))
        self.assertFalse(application.allowed_file('data.zip'))
        self.assertFalse(application.allowed_file('noextension'))


# =============================================================================
# 12. Paramètres
# =============================================================================

class TestParametres(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_save_settings_via_http(self):
        r = self.client.post('/parametres', data={
            'action': 'save_settings',
            'association_name': 'Test Club',
            'location': 'Ville Test',
            'currency': '$',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        settings = db.get_settings()
        self.assertEqual(settings['association_name'], 'Test Club')
        self.assertEqual(settings['currency'], '$')
        # Remettre en place
        db.update_setting('association_name', 'SLAMM')
        db.update_setting('currency', '€')

    def test_export_db(self):
        r = self.client.post('/parametres', data={'action': 'export_db'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/octet-stream', r.content_type)


# =============================================================================
# 13. Routes de mise à jour
# =============================================================================

class TestUpdateRoutes(unittest.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_check_update_returns_json(self):
        """L'endpoint retourne bien du JSON avec les clés attendues."""
        import json as _json
        r = self.client.get('/api/check-update')
        self.assertEqual(r.status_code, 200)
        data = _json.loads(r.data)
        self.assertIn('local_version', data)
        self.assertIn('update_available', data)

    def test_check_update_local_version_matches_file(self):
        """La version locale retournée correspond au fichier VERSION."""
        import json as _json
        r = self.client.get('/api/check-update')
        data = _json.loads(r.data)
        self.assertEqual(data['local_version'], application.get_version())

    def test_admin_update_requires_post(self):
        """La route /admin/update ne répond pas aux GET."""
        r = self.client.get('/admin/update')
        self.assertEqual(r.status_code, 405)


if __name__ == '__main__':
    unittest.main(verbosity=2)

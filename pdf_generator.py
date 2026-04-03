import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)

# ── Palette (thème clair, imprimable) ────────────────────────────────────────
RED       = colors.HexColor('#C8102E')   # rouge SLAMM
HDR_BG    = colors.HexColor('#1E2A3A')   # fond entête de tableau
HDR_TEXT  = colors.white
ROW_ALT   = colors.HexColor('#F4F6F8')   # ligne alternée
ROW_EVEN  = colors.white
BORDER    = colors.HexColor('#CBD5E0')
TEXT      = colors.HexColor('#1A202C')
MUTED     = colors.HexColor('#718096')
GREEN     = colors.HexColor('#16A34A')
RED_NEG   = colors.HexColor('#DC2626')

PAGE_W, PAGE_H = A4
# Largeur utile : 21 cm − 2×1,8 cm marges = 17,4 cm
USABLE_W = PAGE_W - 2 * 1.8 * cm

# ── Styles de paragraphe ──────────────────────────────────────────────────────
_TITLE_STYLE = ParagraphStyle(
    'Title', fontName='Helvetica-Bold', fontSize=22,
    textColor=RED, spaceAfter=2, alignment=TA_LEFT, letterSpacing=2,
)
_SUBTITLE_STYLE = ParagraphStyle(
    'Subtitle', fontName='Helvetica', fontSize=10,
    textColor=MUTED, spaceAfter=6, alignment=TA_LEFT,
)
_HEADING_STYLE = ParagraphStyle(
    'Heading', fontName='Helvetica-Bold', fontSize=11,
    textColor=TEXT, spaceBefore=12, spaceAfter=5, alignment=TA_LEFT,
)
_NORMAL_STYLE = ParagraphStyle(
    'Normal', fontName='Helvetica', fontSize=9,
    textColor=TEXT, spaceAfter=3,
)
_META_STYLE = ParagraphStyle(
    'Meta', fontName='Helvetica', fontSize=8,
    textColor=MUTED, alignment=TA_RIGHT,
)


def _header_elements(title_text, subtitle_text):
    now = datetime.now().strftime('%d/%m/%Y à %H:%M')
    return [
        Paragraph("SLAMM", _TITLE_STYLE),
        Paragraph("Association MMA · Saint-Lunaire", _SUBTITLE_STYLE),
        HRFlowable(width="100%", thickness=1.5, color=RED, spaceAfter=8),
        Paragraph(title_text, ParagraphStyle(
            'ReportTitle', fontName='Helvetica-Bold', fontSize=14,
            textColor=TEXT, spaceAfter=2,
        )),
        Paragraph(f"Généré le {now}", _META_STYLE),
        Spacer(1, 0.4 * cm),
    ]


def _tx_table(transactions, currency='€'):
    # 17,4 cm disponibles : Date | Libellé | Catégorie | Montant
    col_w = [2.0 * cm, 7.5 * cm, 4.0 * cm, 3.9 * cm]
    header = ['Date', 'Libellé', 'Catégorie', 'Montant']
    data = [header]
    for tx in transactions:
        sign = '+' if tx['type'] == 'income' else '−'
        amount_str = f"{sign} {tx['amount']:,.2f} {currency}".replace(',', ' ')
        color_str = '#16A34A' if tx['type'] == 'income' else '#DC2626'
        amt_style = ParagraphStyle(
            'Amt', fontName='Helvetica', fontSize=8,
            textColor=TEXT, alignment=TA_RIGHT,
        )
        data.append([
            tx['date'],
            tx['label'][:55],
            tx.get('category_name') or '—',
            Paragraph(f'<font color="{color_str}">{amount_str}</font>', amt_style),
        ])

    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND',    (0, 0), (-1, 0),  HDR_BG),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  HDR_TEXT),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  8),
        # Lignes alternées
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_EVEN, ROW_ALT]),
        ('TEXTCOLOR',     (0, 1), (-1, -1), TEXT),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        # Grille
        ('GRID',          (0, 0), (-1, -1), 0.4, BORDER),
        ('ALIGN',         (3, 0), (3, -1),  'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _summary_table(income, expense, balance, currency='€'):
    def fmt(v):
        return f"{v:,.2f} {currency}".replace(',', ' ')

    bal_color = GREEN if balance >= 0 else RED_NEG
    data = [
        ['Total entrées',  fmt(income)],
        ['Total sorties',  fmt(expense)],
        ['Solde net',      fmt(balance)],
    ]
    tbl = Table(data, colWidths=[6 * cm, 4 * cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), ROW_ALT),
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#EEF2F7')),
        ('TEXTCOLOR',     (0, 0), (-1, -1), TEXT),
        ('TEXTCOLOR',     (1, 0), (1, 0),   GREEN),
        ('TEXTCOLOR',     (1, 1), (1, 1),   RED_NEG),
        ('TEXTCOLOR',     (1, -1), (1, -1), bal_color),
        ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.4, BORDER),
        ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ]))
    return tbl


def generate_monthly_report(transactions, year, month, currency='€'):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    MONTHS_FR = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    month_name = MONTHS_FR[month - 1]

    elements = _header_elements(
        f"Rapport mensuel — {month_name} {year}",
        f"Transactions du {month_name} {year}",
    )
    income  = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = income - expense

    elements.append(Paragraph("Synthèse", _HEADING_STYLE))
    elements.append(_summary_table(income, expense, balance, currency))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(f"Transactions ({len(transactions)})", _HEADING_STYLE))
    if transactions:
        elements.append(_tx_table(transactions, currency))
    else:
        elements.append(Paragraph("Aucune transaction ce mois.", _NORMAL_STYLE))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_annual_report(transactions, budget_data, year, currency='€'):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    elements = _header_elements(f"Rapport annuel {year}", f"Exercice {year}")

    income  = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = income - expense

    elements.append(Paragraph("Synthèse annuelle", _HEADING_STYLE))
    elements.append(_summary_table(income, expense, balance, currency))
    elements.append(Spacer(1, 0.5 * cm))

    if budget_data:
        elements.append(Paragraph("Budget vs Réalisé", _HEADING_STYLE))
        # 17,4 cm : Catégorie | Type | Budget | Réalisé | Écart | % cons.
        b_col_w = [4.2*cm, 1.8*cm, 2.8*cm, 2.8*cm, 2.8*cm, 3.0*cm]
        bdata = [['Catégorie', 'Type', 'Budget', 'Réalisé', 'Écart', '% cons.']]
        def fmt(v): return f"{v:,.2f} {currency}".replace(',', ' ')
        for row in budget_data:
            ecart = row['actual_amount'] - row['budget_amount']
            pct   = (row['actual_amount'] / row['budget_amount'] * 100) if row['budget_amount'] else 0
            bdata.append([
                row['category_name'],
                'Entrée' if row['type'] == 'income' else 'Sortie',
                fmt(row['budget_amount']),
                fmt(row['actual_amount']),
                fmt(ecart),
                f"{pct:.0f}%",
            ])
        btbl = Table(bdata, colWidths=b_col_w, repeatRows=1)
        btbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  HDR_BG),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  HDR_TEXT),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_EVEN, ROW_ALT]),
            ('TEXTCOLOR',     (0, 1), (-1, -1), TEXT),
            ('GRID',          (0, 0), (-1, -1), 0.4, BORDER),
            ('ALIGN',         (2, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ]))
        elements.append(btbl)
        elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph(f"Toutes les transactions ({len(transactions)})", _HEADING_STYLE))
    if transactions:
        elements.append(_tx_table(transactions, currency))
    else:
        elements.append(Paragraph("Aucune transaction cette année.", _NORMAL_STYLE))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_season_report(transactions, start_year, currency='€'):
    """Rapport couvrant la saison sportive : sep start_year → août start_year+1."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    label  = f"Saison {start_year}–{start_year + 1}"
    period = f"1er septembre {start_year} — 31 août {start_year + 1}"
    elements = _header_elements(f"Rapport de saison {start_year}–{start_year + 1}", period)

    income  = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = income - expense

    elements.append(Paragraph(f"Synthèse — {label}", _HEADING_STYLE))
    elements.append(_summary_table(income, expense, balance, currency))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(f"Toutes les transactions ({len(transactions)})", _HEADING_STYLE))
    if transactions:
        elements.append(_tx_table(transactions, currency))
    else:
        elements.append(Paragraph("Aucune transaction sur cette saison.", _NORMAL_STYLE))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_receipt(transaction, currency='€'):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9,
                                 textColor=MUTED, spaceAfter=1)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=11,
                                 textColor=TEXT, spaceAfter=10)

    elements = _header_elements("Reçu de transaction", "")

    typ_label  = "Entrée" if transaction['type'] == 'income' else "Sortie"
    sign       = '+' if transaction['type'] == 'income' else '−'
    amount_str = f"{sign} {transaction['amount']:,.2f} {currency}".replace(',', ' ')
    amt_color  = '#16A34A' if transaction['type'] == 'income' else '#DC2626'

    fields = [
        ('Référence', f"#{transaction['id']}"),
        ('Date',      transaction['date']),
        ('Libellé',   transaction['label']),
        ('Type',      typ_label),
        ('Catégorie', transaction.get('category_name') or '—'),
        ('Montant',   f'<font color="{amt_color}" size="14"><b>{amount_str}</b></font>'),
        ('Notes',     transaction.get('notes') or '—'),
    ]
    for lbl, val in fields:
        elements.append(Paragraph(lbl, label_style))
        elements.append(Paragraph(val, value_style))

    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    doc.build(elements)
    buffer.seek(0)
    return buffer

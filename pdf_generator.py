import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Couleurs SLAMM
RED = colors.HexColor('#C8102E')
DARK_BG = colors.HexColor('#1A1A1A')
DARK_HEADER = colors.HexColor('#111111')
BORDER = colors.HexColor('#2A2A2A')
GREEN = colors.HexColor('#22C55E')
RED_NEG = colors.HexColor('#EF4444')
GREY = colors.HexColor('#888888')
WHITE = colors.white
BLACK = colors.HexColor('#0A0A0A')
LIGHT = colors.HexColor('#F0F0F0')

PAGE_W, PAGE_H = A4

# Styles calculés une seule fois au chargement du module
_TITLE_STYLE = ParagraphStyle(
    'SLAMMTitle',
    fontName='Helvetica-Bold',
    fontSize=22,
    textColor=RED,
    spaceAfter=2,
    alignment=TA_LEFT,
    letterSpacing=3,
)
_SUBTITLE_STYLE = ParagraphStyle(
    'SLAMMSubtitle',
    fontName='Helvetica',
    fontSize=10,
    textColor=GREY,
    spaceAfter=6,
    alignment=TA_LEFT,
)
_HEADING_STYLE = ParagraphStyle(
    'SLAMMHeading',
    fontName='Helvetica-Bold',
    fontSize=13,
    textColor=LIGHT,
    spaceBefore=14,
    spaceAfter=6,
    alignment=TA_LEFT,
)
_NORMAL_STYLE = ParagraphStyle(
    'SLAMMNormal',
    fontName='Helvetica',
    fontSize=9,
    textColor=LIGHT,
    spaceAfter=3,
)
_META_STYLE = ParagraphStyle(
    'SLAMMMeta',
    fontName='Helvetica',
    fontSize=8,
    textColor=GREY,
    alignment=TA_RIGHT,
)


def _header_elements(title_text, subtitle_text):
    title_style, subtitle_style, meta_style = _TITLE_STYLE, _SUBTITLE_STYLE, _META_STYLE
    now = datetime.now().strftime('%d/%m/%Y à %H:%M')
    elements = [
        Paragraph("SLAMM", title_style),
        Paragraph("Association MMA · Saint-Lunaire", subtitle_style),
        HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=8),
        Paragraph(title_text, ParagraphStyle(
            'ReportTitle', fontName='Helvetica-Bold', fontSize=14,
            textColor=LIGHT, spaceAfter=2,
        )),
        Paragraph(f"Généré le {now}", meta_style),
        Spacer(1, 0.4 * cm),
    ]
    return elements


def _tx_table(transactions, currency='€'):
    normal_style = _NORMAL_STYLE
    header = ['Date', 'Libellé', 'Catégorie', 'Montant']
    data = [header]
    for tx in transactions:
        amount = tx['amount']
        sign = '+' if tx['type'] == 'income' else '−'
        amount_str = f"{sign} {amount:,.2f} {currency}".replace(',', ' ')
        color_str = '#22C55E' if tx['type'] == 'income' else '#EF4444'
        data.append([
            tx['date'],
            tx['label'][:50],
            tx.get('category_name') or '—',
            Paragraph(f'<font color="{color_str}">{amount_str}</font>', ParagraphStyle(
                'Amount', fontName='Helvetica', fontSize=8,
                textColor=LIGHT, alignment=TA_RIGHT,
            )),
        ])

    col_widths = [2.2 * cm, 8.5 * cm, 4.0 * cm, 3.5 * cm]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), GREY),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [DARK_BG, colors.HexColor('#161616')]),
        ('TEXTCOLOR', (0, 1), (-1, -1), LIGHT),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ])
    tbl.setStyle(style)
    return tbl


def _summary_table(income, expense, balance, currency='€'):
    def fmt(v):
        return f"{v:,.2f} {currency}".replace(',', ' ')

    data = [
        ['Total entrées', fmt(income)],
        ['Total sorties', fmt(expense)],
        ['Solde', fmt(balance)],
    ]
    tbl = Table(data, colWidths=[6 * cm, 4 * cm])
    bal_color = GREEN if balance >= 0 else RED_NEG
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -2), DARK_BG),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1F1F1F')),
        ('TEXTCOLOR', (0, 0), (-1, -1), LIGHT),
        ('TEXTCOLOR', (1, 0), (1, 0), GREEN),
        ('TEXTCOLOR', (1, 1), (1, 1), RED_NEG),
        ('TEXTCOLOR', (1, -1), (1, -1), bal_color),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
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

    heading_style, normal_style = _HEADING_STYLE, _NORMAL_STYLE
    elements = _header_elements(
        f"Rapport mensuel — {month_name} {year}",
        f"Transactions du {month_name} {year}"
    )

    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = income - expense

    elements.append(Paragraph("Synthèse", heading_style))
    elements.append(_summary_table(income, expense, balance, currency))
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph(f"Transactions ({len(transactions)})", heading_style))
    if transactions:
        elements.append(_tx_table(transactions, currency))
    else:
        elements.append(Paragraph("Aucune transaction ce mois.", normal_style))

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

    heading_style, normal_style = _HEADING_STYLE, _NORMAL_STYLE
    elements = _header_elements(f"Rapport annuel {year}", f"Exercice {year}")

    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = income - expense

    elements.append(Paragraph("Synthèse annuelle", heading_style))
    elements.append(_summary_table(income, expense, balance, currency))
    elements.append(Spacer(1, 0.5 * cm))

    if budget_data:
        elements.append(Paragraph("Budget vs Réalisé", heading_style))
        bheader = ['Catégorie', 'Type', 'Budget', 'Réalisé', 'Écart', '% cons.']
        bdata = [bheader]
        for row in budget_data:
            ecart = row['actual_amount'] - row['budget_amount']
            pct = (row['actual_amount'] / row['budget_amount'] * 100) if row['budget_amount'] else 0
            typ_label = 'Entrée' if row['type'] == 'income' else 'Sortie'
            def fmt(v): return f"{v:,.2f} {currency}".replace(',', ' ')
            bdata.append([
                row['category_name'],
                typ_label,
                fmt(row['budget_amount']),
                fmt(row['actual_amount']),
                fmt(ecart),
                f"{pct:.0f}%",
            ])
        btbl = Table(bdata, colWidths=[4.5*cm, 1.8*cm, 3*cm, 3*cm, 3*cm, 2*cm], repeatRows=1)
        btbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DARK_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), GREY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [DARK_BG, colors.HexColor('#161616')]),
            ('TEXTCOLOR', (0, 1), (-1, -1), LIGHT),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(btbl)
        elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph(f"Toutes les transactions ({len(transactions)})", heading_style))
    if transactions:
        elements.append(_tx_table(transactions, currency))
    else:
        elements.append(Paragraph("Aucune transaction cette année.", normal_style))

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
                                 textColor=GREY, spaceAfter=1)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=11,
                                 textColor=LIGHT, spaceAfter=10)

    elements = _header_elements("Reçu de transaction", "")

    typ_label = "Entrée" if transaction['type'] == 'income' else "Sortie"
    amount = transaction['amount']
    sign = '+' if transaction['type'] == 'income' else '−'
    amount_str = f"{sign} {amount:,.2f} {currency}".replace(',', ' ')
    amt_color = '#22C55E' if transaction['type'] == 'income' else '#EF4444'

    fields = [
        ('Référence', f"#{transaction['id']}"),
        ('Date', transaction['date']),
        ('Libellé', transaction['label']),
        ('Type', typ_label),
        ('Catégorie', transaction.get('category_name') or '—'),
        ('Montant', f'<font color="{amt_color}" size="14"><b>{amount_str}</b></font>'),
        ('Notes', transaction.get('notes') or '—'),
    ]

    for lbl, val in fields:
        elements.append(Paragraph(lbl, label_style))
        elements.append(Paragraph(val, value_style))

    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# coding: utf-8
import StringIO
import re

# reportlab imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, StyleSheet1, ParagraphStyle
from reportlab.lib.colors import white, black
from reportlab.rl_config import defaultPageSize
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from reportlab.lib.colors import HexColor


def page(canvas, doc):
    canvas.saveState()

    story = []
    pdf = StringIO.StringIO()

    stylesheet = getSampleStyleSheet()

    stylesheet.add(ParagraphStyle(
        name='MyHeading1',
        alignment=TA_CENTER,
        fontSize=14,
        fontName="Helvetica-Bold"))

    stylesheet.add(ParagraphStyle(
        name='MyHeading2',
        fontSize=11,
        fontName="Helvetica-Bold"))

    stylesheet.add(ParagraphStyle(
        name='MyNormal',
        fontSize=10,
        fontName="Helvetica"))

    stylesheet.add(ParagraphStyle(
        name='MySmall',
        fontSize=8,
        fontName="Helvetica"))

    stylesheet.add(ParagraphStyle(
        name='MyBorder',
        backColor = "#FFFF00",
        borderColor = "#000000",
        borderWidth = 1,
        borderPadding = (7, 2, 20),
        ))

    styleH = stylesheet["MyHeading1"]
    styleH2 = stylesheet["MyHeading2"]
    styleN = stylesheet["MyNormal"]
    styleS = stylesheet["MySmall"]
    styleB = stylesheet["MyBorder"]

    logo = Image("/Users/Kai/Pictures/Demmelhuber/test.jpg")
    header = Table([["Rechnung", logo]], (340, 178))
    header.setStyle(
            TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (0, 0), "BOTTOM"),
                ('ALIGN', (0, 0), (-1, -1), "RIGHT"),
                ('FONTSIZE', (0, 0), (0, 0), 16),
                ('FONT', (0, 0), (0, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (0, 0), 20),
            ])
    )

    story.append(header)

    f = Frame(39, 700, 518, 140, showBoundary=0)
    f.addFromList(story, canvas)

    canvas.restoreState()


def create_invoice():
    pdf = StringIO.StringIO()

    doc = SimpleDocTemplate(pdf)
    doc.leftMargin=39
    doc.rightMargin=39
    doc.topMargin=130
    doc.bottomMargin=140

    table_style = TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#DDDDDD")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

        ('ALIGN', (0, 0), (-2, -1), 'LEFT'),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ])


    story = []
    requisition_items = [["TeileNr.", "Menge", "Bezeichnung", "Preis/Einheit"]]

    for i in xrange(100):
        requisition_items.append(["", "", "", ""])

    requisition_table = Table(requisition_items, (50, 50, 343, 75))
    requisition_table.setStyle(table_style)

    story.append(requisition_table)

    doc.build(story, onFirstPage=page, onLaterPages=page)
    pdf.seek(0)
    return pdf


def prepare_text(text):
    text = re.subn("\n", "<br />", text)
    return text[0]

if __name__ == "__main__":
    pdf = create_invoice()

    fh = open("test.pdf", "w")
    fh.write(pdf.read())
    fh.close()

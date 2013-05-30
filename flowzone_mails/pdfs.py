# coding: utf-8
import datetime
import StringIO
import re

# django imports
from django.conf import settings

# lfs imports
from lfs.core.templatetags.lfs_tags import currency
from lfs.core.templatetags.lfs_tags import packages

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
    name='MyNormalRight',
    fontSize=10,
    alignment=TA_RIGHT,
    fontName="Helvetica"))

stylesheet.add(ParagraphStyle(
    name='MySmall',
    fontSize=8,
    fontName="Helvetica"))

stylesheet.add(ParagraphStyle(
    name='MyBold',
    fontSize=10,
    fontName="Helvetica-Bold"))

in_order_items_style = TableStyle([
    ('GRID', (0, 0), (-1, -3), 0.5, HexColor("#AAAAAA")),
    ('GRID', (-1, -2), (-1, -1), 0.5, HexColor("#AAAAAA")),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('FONTSIZE', (0, -1), (-1, -1), 8),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTNAME', (-2, -2), (-1, -2), 'Helvetica-Bold'),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#DDDDDD")),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
])

dn_order_items_style = TableStyle([
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#AAAAAA")),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#DDDDDD")),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
])

footer_style = TableStyle([
    ('FONTSIZE', (0, 0), (-1, -1), 7),
    ('BOTTOMPADDING', (0, 0), (-1, -1), -1.5),
    ('TOPPADDING', (0, 0), (-1, -1), -1.5),
])

styleH = stylesheet["MyHeading1"]
styleH2 = stylesheet["MyHeading2"]
styleN = stylesheet["MyNormal"]
styleNR = stylesheet["MyNormalRight"]
styleS = stylesheet["MySmall"]
styleB = stylesheet["MyBold"]


class Invoice(object):
    def __init__(self, order):
        self.order = order

    def create_pdf(self):
        pdf = StringIO.StringIO()

        doc = SimpleDocTemplate(pdf)
        doc.leftMargin=31
        doc.rightMargin=31
        doc.topMargin=390
        doc.bottomMargin=110

        story = []
        order_items = [["Artikelnr.", "Name", "Menge", "Preis", "Summe"]]
        for item in self.order.items.all():
            # Amount
            amount = str(item.amount)
            if item.product.unit:
                amount += " " + item.product.unit
            if item.product.active_packing_unit:
                amount += "\n(" + str(packages(item)) + " " + item.product.packing_unit_unit + ")"
            # Name
            item_name = item.product_name
            for property in item.product.get_displayed_properties():
                item_name += "\n" + property["title"] + ": " + property["value"] + " " + property["unit"]
            for property in item.product.get_variant_properties():
                item_name += "\n" + property["title"] + ": " + property["value"] + " " + property["unit"]
            if item.product.is_configurable_product():
                for property in item.get_properties():
                    item_name += "\n" + property["title"] + ": " + property["value"] + property["unit"] + " " + property["price"]
            price = currency(item.product_price_gross)
            if item.product.price_unit:
                price += " / " + item.product.price_unit
            total = currency(item.price_gross)
            order_items.append([item.product.sku, item_name, amount, price, total])

        if self.order.voucher_number:
            order_items.append(["", "Voucher", "1", currency(self.order.voucher_price), currency(self.order.voucher_price)])

        order_items.append(["", "Versandart (" + self.order.shipping_method.name + ")", "1", currency(self.order.shipping_price), currency(self.order.shipping_price)])
        order_items.append(["", "Zahlungsweise (" + self.order.payment_method.name + ")", "1", currency(self.order.payment_price), currency(self.order.payment_price)])

        order_items.append(["", "", "", "Summe", currency(self.order.price)])
        order_items.append(["", "", "", "Inkl. MwSt", currency(self.order.tax)])

        order_items_table = Table(order_items, (80, 238, 60, 70, 70))
        order_items_table.setStyle(in_order_items_style)

        story.append(order_items_table)
        story.append(Spacer(1, 40))

        # END
        story.append(Paragraph(getattr(settings, "IN_END"), styleN))

        doc.build(story, onFirstPage=self.page, onLaterPages=self.page)
        pdf.seek(0)
        return pdf

    def page(self, canvas, doc):
        canvas.saveState()

        pdf = StringIO.StringIO()

        # Logo
        f = Frame(39, 700, 518, 140, showBoundary=0)
        f.addFromList([Image(getattr(settings, "IN_LOGO"))], canvas)

        # Address Line
        f = Frame(31, 680, 80, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "IN_SENDER_1"), styleB)], canvas)

        f = Frame(102, 678, 300, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "IN_SENDER_2"), styleS)], canvas)

        # Receiver
        receiver = ""
        if self.order.invoice_address.company_name:
            receiver += self.order.invoice_address.company_name + "<br/>"
        receiver += self.order.invoice_address.firstname + " " + self.order.invoice_address.lastname + "<br/>"
        receiver += self.order.invoice_address.line1 + "<br/><br/>"
        receiver += self.order.invoice_address.zip_code + " " + self.order.invoice_address.city

        f = Frame(31, 600, 300, 80, showBoundary=0)
        f.addFromList([Paragraph(receiver, styleB)], canvas)

        # Date
        now = datetime.datetime.now()
        f = Frame(31, 580, 518, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "IN_CITY") + ", den " + now.strftime("%d.%m.%Y"), styleNR)], canvas)

        # Subject
        f = Frame(31, 550, 518, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "IN_SUBJECT"), styleB)], canvas)

        # Text
        f = Frame(31, 400, 518, 125, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "IN_START_1") % {"lastname": self.order.invoice_address.lastname}, styleN)], canvas)

        f = Frame(31, 380, 518, 125, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "IN_START_2"), styleN)], canvas)

        # Footer
        story = []
        footer = getattr(settings, "IN_FOOTER")

        footer = Table(footer, (205, 200, 127))
        footer.setStyle(footer_style)

        story.append(footer)
        f = Frame(39, 0, 518, 100, showBoundary=0)
        f.addFromList(story, canvas)

        canvas.restoreState()

# TODO: create class structure?
class DeliveryNote(object):
    def __init__(self, order):
        self.order = order

    def create_pdf(self):
        pdf = StringIO.StringIO()

        doc = SimpleDocTemplate(pdf)
        doc.leftMargin=31
        doc.rightMargin=31
        doc.topMargin=390
        doc.bottomMargin=110

        story = []
        order_items = [["Artikelnr.", "Name", "Menge", "Preis", "Summe"]]
        for item in self.order.items.all():
            amount = str(item.amount) + " " + item.product.unit
            price = currency(item.product_price_gross)
            total = currency(item.price_gross)
            order_items.append([item.product.sku, item.product_name, amount, price, total])

        order_items_table = Table(order_items, (80, 238, 60, 70, 70))
        order_items_table.setStyle(dn_order_items_style)

        story.append(order_items_table)
        story.append(Spacer(1, 40))

        # END
        story.append(Paragraph(getattr(settings, "DN_END"), styleN))

        doc.build(story, onFirstPage=self.page, onLaterPages=self.page)
        pdf.seek(0)
        return pdf

    def page(self, canvas, doc):
        canvas.saveState()

        pdf = StringIO.StringIO()

        # Logo
        f = Frame(39, 700, 518, 140, showBoundary=0)
        f.addFromList([Image(getattr(settings, "DN_LOGO"))], canvas)

        # Address Line
        f = Frame(31, 680, 80, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "DN_SENDER_1"), styleB)], canvas)

        f = Frame(102, 678, 300, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "DN_SENDER_2"), styleS)], canvas)

        # Receiver
        receiver = ""
        if self.order.invoice_address.company_name:
            receiver += self.order.invoice_address.company_name + "<br/>"
        receiver += self.order.invoice_address.firstname + " " + self.order.invoice_address.lastname + "<br/>"
        receiver += self.order.invoice_address.line1 + "<br/><br/>"
        receiver += self.order.invoice_address.zip_code + " " + self.order.invoice_address.city

        f = Frame(31, 600, 300, 80, showBoundary=0)
        f.addFromList([Paragraph(receiver, styleB)], canvas)

        # Date
        now = datetime.datetime.now()
        f = Frame(31, 580, 518, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "DN_CITY") + ", den " + now.strftime("%d.%m.%Y"), styleNR)], canvas)

        # Subject
        f = Frame(31, 550, 518, 25, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "DN_SUBJECT"), styleB)], canvas)

        # Text
        f = Frame(31, 400, 518, 125, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "DN_START_1") % {"lastname": self.order.invoice_address.lastname}, styleN)], canvas)

        f = Frame(31, 380, 518, 125, showBoundary=0)
        f.addFromList([Paragraph(getattr(settings, "DN_START_2"), styleN)], canvas)

        # Footer
        story = []
        footer = getattr(settings, "DN_FOOTER")

        footer = Table(footer, (205, 200, 127))
        footer.setStyle(footer_style)

        story.append(footer)
        f = Frame(39, 0, 518, 100, showBoundary=0)
        f.addFromList(story, canvas)

        canvas.restoreState()

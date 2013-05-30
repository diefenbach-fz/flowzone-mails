# python imports
from optparse import make_option

# django imports
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dn',
            action='store_true',
            dest='delivery_note',
            default=False,
            help='Create Invoice'),
        )

    def handle(self, *args, **options):
        from lfs.order.models import Order
        from flowzone_mails.pdfs import Invoice
        from flowzone_mails.pdfs import DeliveryNote

        if options["delivery_note"]:
            dn = DeliveryNote(Order.objects.all().order_by("-id")[0])
            pdf = dn.create_pdf()
        else:
            i = Invoice(Order.objects.all().order_by("-id")[0])
            pdf = i.create_pdf()

        fh = open("pdf.pdf", "w")
        fh.write(pdf.read())
        fh.close()

# django imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template import RequestContext
from django.template.base import TemplateDoesNotExist
from django.template.loader import render_to_string

# lfs imports
from lfs.core.signals import order_submitted


@receiver(order_submitted)
def order_submitted_listener(sender, **kwargs):
    """Listen to order submitted signal.
    """
    order = sender.get("order")
    request = sender.get("request")

    if getattr(settings, 'LFS_SEND_ORDER_MAIL_ON_CHECKOUT', True):
        send_delivery_note(request, order)


def send_delivery_note(request, order):
    import lfs.core.utils
    shop = lfs.core.utils.get_default_shop()
    from flowzone_mails.pdfs import DeliveryNote


    try:
        subject = render_to_string("lfs/mail/send_delivery_note_subject.txt", {"order": order})
    except TemplateDoesNotExist:
        subject = _(u"Your order has been received")

    from_email = shop.from_email
    to = [shop.delivery_note_mail]
    bcc = shop.get_notification_emails()

    # text
    text = render_to_string("lfs/mail/send_delivery_note.txt", RequestContext(request, {"order": order}))
    mail = EmailMultiAlternatives(
        subject=subject, body=text, from_email=from_email, to=to, bcc=bcc)

    # html
    html = render_to_string("lfs/mail/send_delivery_note.html", RequestContext(request, {
        "order": order
    }))

    mail.attach_alternative(html, "text/html")

    # Create PDF
    pdf = DeliveryNote(order).create_pdf()
    mail.attach("Lieferschein", pdf.read(), "application/pdf")

    mail.send(fail_silently=True)

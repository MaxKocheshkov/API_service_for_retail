from django.core.mail import EmailMessage
from django.conf import settings

def send_email(title, body, to, files_path=None):
    email = EmailMessage(
        title,
        body,
        f'Магазин <{settings.EMAIL_HOST_USER}>',
        to
    )

    if files_path:
        for file_path in files_path:
            email.attach_file(file_path)

    email.send()
import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail
import aiosmtplib
from email.message import EmailMessage


class SendgridEmailSender:
    def __init__(self, api_key, from_email):
        self.from_email = Email(from_email)
        self._worker = sendgrid.SendGridAPIClient(api_key)

    def send_message(self, message):
        content = Content("text/plain", message.content)
        mail = Mail(self.from_email, message.to_email, message.subject, content)
        self._worker.client.mail.send.post(request_body=mail.get())  # noqa!


class EmailSender:
    def __init__(self, host, port, sender):
        self.from_email = sender
        self._worker = aiosmtplib.SMTP(hostname=host, port=port)

    async def send_message(self, message):
        email_message = EmailMessage()
        email_message["From"] = self.from_email
        email_message["To"] = message.to_email
        email_message["Subject"] = message.subject
        email_message.set_content(message.content)
        self._worker.send_message(email_message)

    async def connect(self):
        await self._worker.connect()

    async def close(self):
        await self._worker.quit()

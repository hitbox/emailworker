import smtplib
from email.message import EmailMessage

def sendemail(host, fromaddr, toaddrs, body, subject=None):
    """
    Send an email.

    :param host: SMTP host.
    :type host: str

    :param fromaddr: The from address.
    :type fromaddr: str

    :param toaddrs: The to address(es). Comma-separated if more than one.
    :type toaddrs: str

    :param body: The body of the email.
    :type body: str

    :param subject: The subject of the email. An empty string is used if None.
                    Default: None.
    :type subject: str or None
    """
    emailmessage = EmailMessage()
    emailmessage['From'] = fromaddr
    emailmessage['To'] = toaddrs
    emailmessage['Subject'] = subject if subject is not None else ''
    emailmessage.set_content(body)
    server = smtplib.SMTP(host)
    server.send_message(emailmessage)
    server.quit()

import argparse
import inspect
import json
import logging
import logging.config
import smtplib
import types
from email.message import EmailMessage
from pathlib import Path

import pika

serializer = json.dumps
deserializer = json.loads

def bind_and_call(func, data):
    """
    Bind the keys of `data` to the arguments of `func` and call `func` with
    those arguments.

    :param func: A callable.
    :type func: callable

    :param data: A mapping object.
    :type data: dict
    """
    bound = inspect.signature(func).bind(**data)
    return func(*bound.args, **bound.kwargs)

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

class Config(dict):
    """
    A clone of the Flask configuration object.
    """
    def from_pyfile(self, filename):
        """
        Pull UPPERCASE attributes from `filename` and store in self.

        :param filename: Path to `.py` file.
        :type filename: str or pathlib.Path
        """
        d = types.ModuleType('config')
        d.__file__ = filename
        with open(filename, 'rb') as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
        self.from_object(d)
        return True

    def from_object(self, obj):
        """
        Pull UPPERCASE attributes from `obj` and store in self.

        :type obj: object
        """
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)


class DefaultConfig:
    """
    Configuration for use with RabbitMQ and SMTP running on localhost.
    """
    RABBITMQ_HOST = 'localhost'
    SMTP_HOST = 'localhost'
    QUEUE = 'emails'


class Worker:
    """
    A task worker that sends emails.
    """
    def __init__(self, rabbitmq_host, smtp_host, queue):
        """
        :type rabbitmq_host: str
        :type smtp_host: str
        :param queue: The rabbitmq queue name.
        :type queue: str
        """
        self.rabbitmq_host = rabbitmq_host
        self.smtp_host = smtp_host
        self.queue = queue

    def ack_and_send_email(self, channel, method, properties, body):
        """
        Acknowledge message and attempt to send email. All exceptions are
        caught and logged.
        """
        channel.basic_ack(delivery_tag = method.delivery_tag)
        kwargs = deserializer(body)
        kwargs['host'] = self.smtp_host
        try:
            bind_and_call(sendemail, kwargs)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            logger = logging.getLogger('emailworker.Worker')
            logger.exception('%s', kwargs)

    def start(self):
        """
        Start the message consumer.
        """
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbitmq_host)
        )
        channel = connection.channel()
        channel.queue_declare(queue=self.queue, durable=True)
        channel.basic_consume(self.ack_and_send_email, queue=self.queue)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.close()


def main():
    """
    Email Worker.
    """
    parser = argparse.ArgumentParser(prog='emailworker', description=main.__doc__)
    args = parser.parse_args()

    config = Config()
    config.from_object(DefaultConfig)

    path = Path("./instance/config.py")
    if path.exists():
        config.from_pyfile(path)

    if 'LOGGING_CONF_DICT' in config:
        logging.config.dictConfig(config['LOGGING_CONF_DICT'])

    worker = Worker(config['RABBITMQ_HOST'], config['SMTP_HOST'], config['QUEUE'])
    worker.start()

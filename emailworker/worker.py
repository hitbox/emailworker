import logging
import logging.config

import pika

from .email import sendemail
from .util import bind_and_call
from .util import deserializer

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
        logger = logging.getLogger('emailworker.Worker')
        channel.basic_ack(delivery_tag = method.delivery_tag)
        logger.debug('channel.basic_ack(delivery_tag = %s)', method.delivery_tag)
        kwargs = deserializer(body)
        kwargs['host'] = self.smtp_host
        logger.debug('deserialized: %r', kwargs)
        try:
            bind_and_call(sendemail, kwargs)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            logger.exception('%s', kwargs)
        else:
            logger.debug('sendemail successfull')

    def start(self):
        """
        Start the message consumer.
        """
        logger = logging.getLogger('emailworker.Worker')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbitmq_host)
        )
        channel = connection.channel()
        channel.queue_declare(queue=self.queue, durable=True)
        channel.basic_consume(self.ack_and_send_email, queue=self.queue)
        # don't know how to log this message after we've really started
        logger.info('started')
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info('closing')
            channel.close()

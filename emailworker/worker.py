import logging

import pika

from .email import sendemail
from .util import bind_and_call
from .util import deserializer

class Worker:
    """
    A task worker that sends emails.
    """
    def __init__(self,
            rabbitmq_host,
            rabbitmq_virtual_host,
            rabbitmq_username,
            rabbitmq_password,
            queue,
            smtp_host,
        ):
        """
        :type rabbitmq_host: str
        :type smtp_host: str
        :param queue: The rabbitmq queue name.
        :type queue: str
        """
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_virtual_host = rabbitmq_virtual_host
        self.rabbitmq_username = rabbitmq_username
        self.rabbitmq_password = rabbitmq_password
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
            pika.ConnectionParameters(
                host = self.rabbitmq_host,
                virtual_host = self.rabbitmq_virtual_host,
                credentials = pika.PlainCredentials(
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                )
            )
        )
        channel = connection.channel()
        channel.queue_declare(
            queue = self.queue,
            durable = True,
        )
        channel.queue_bind(exchange = self.queue, queue = self.queue)
        channel.basic_consume(self.ack_and_send_email, queue=self.queue)
        # don't know how to log this message after we've really started
        logger.info('RabbitMQ Host: %s' % self.rabbitmq_host)
        logger.info('RabbitMQ Virtual Host: %s' % self.rabbitmq_virtual_host)
        logger.info('RabbitMQ Username: %s' % self.rabbitmq_username)
        logger.info('RabbitMQ Queue: %s' % self.queue)
        logger.info('STMP Host: %s' % self.smtp_host)
        logger.info('started')
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info('closing')
            channel.close()

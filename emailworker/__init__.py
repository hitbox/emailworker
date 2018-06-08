import argparse
import inspect
import json
import logging
import logging.config
import smtplib
from configparser import ConfigParser

import pika

# NOTE: disabling interpolation because of logging options
config = ConfigParser(interpolation=None)

def bind_and_call(func, data):
    bound = inspect.signature(func).bind(**data)
    return func(*bound.args, **bound.kwargs)

def setup():
    """
    Setup configuration.
    """
    files = config.read(['default.cfg', 'instance/config.cfg'])
    if 'loggers' in config:
        logging.config.fileConfig(config)
    logger = logging.getLogger('emailworker')
    if files:
        logger.info('successfully read %s', files)
    else:
        logger.info('using config defaults')
    for section in config.sections():
        for key, value in config[section].items():
            logger.info('config: [%s] %s = %r', section, key, value)

def sendemail(fromaddr, toaddrs, msg):
    """
    Send email using configured smtp_host.
    """
    if not config['emailworker'].getboolean('dryrun'):
        server = smtplib.SMTP(config['emailworker']['smtp_host'])
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
    logger = logging.getLogger('emailworker.send')
    logger.info('fromaddr = %r, toaddrs = %r, msg = %r', fromaddr, toaddrs, msg)

def publish(fromaddr, toaddrs, msg):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config['emailworker']['rabbitmq_host'])
    )
    channel = connection.channel()
    channel.basic_publish(
        exchange = '',
        routing_key = config['emailworker']['queue_name'],
        body = json.dumps(
            dict(
                fromaddr = fromaddr,
                toaddrs = toaddrs,
                msg = msg
            )
        )
    )
    channel.close()

def worker(channel, method, properties, body):
    """
    Deserialize message data and call `sendemail`.
    """
    logger = logging.getLogger('emailworker.worker')
    bind_and_call(sendemail, json.loads(body))
    channel.basic_ack(delivery_tag = method.delivery_tag)
    logger.info('message acknowledged')

def start():
    """
    Start the message consumer.
    """
    logger = logging.getLogger('emailworker.start')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config['emailworker']['rabbitmq_host'])
    )
    channel = connection.channel()
    channel.queue_declare(queue=config['emailworker']['queue_name'], durable=True)

    channel.basic_consume(worker, queue=config['emailworker']['queue_name'])
    logger.info('starting worker')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.close()
        logger.info('channel closed')

def main():
    """
    Email Worker.
    """
    parser = argparse.ArgumentParser(prog='emailworker', description=main.__doc__)
    parser.add_argument('--dryrun', action='store_true')
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser('publish')
    subparser.add_argument('fromaddr')
    subparser.add_argument('toaddrs')
    subparser.add_argument('msg')
    subparser.set_defaults(func=publish)

    subparser = subparsers.add_parser('start')
    subparser.set_defaults(func=start)

    args = parser.parse_args()

    if 'func' not in args:
        parser.error('sub-command is required.')

    setup()

    config['emailworker']['dryrun'] = 'yes' if args.dryrun else 'no'
    del args.dryrun

    func = args.func
    del args.func

    bind_and_call(func, vars(args))

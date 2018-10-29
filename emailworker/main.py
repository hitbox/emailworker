import argparse
import inspect
import json
import logging
import logging.config
import sys
from pathlib import Path
from configparser import ConfigParser

import pika

from .config import Config
from .util import bind_and_call
from .worker import Worker

def load_config(config, rabbitmq_config):
    """
    Load application config from `config` and RabbitMQ config from
    `rabbitmq_config`, returning `configparser.ConfigParser` object with loaded
    values.

    :param config: Path to app config file.
    :type config: pathlib.Path, str

    :param rabbitmq_config: Path to RabbitMQ config file.
    :type rabbitmq_config: pathlib.Path, str
    """
    _config = Config()

    if Path(config).exists():
        _config.from_pyfile(config)

    if 'LOGGING_CONF_DICT' in _config:
        logging.config.dictConfig(_config['LOGGING_CONF_DICT'])

    rmq_config = ConfigParser()
    rmq_config.read(rabbitmq_config)
    _config.update(**rmq_config)

    return _config

def start_worker(config):
    """
    Start emailworker to consume messages and send emails.

    :param config: Mapping of RabbitMQ configuration.
    :type config: mapping
    """
    worker = Worker(
        config['connection_parameters']['host'],
        config['connection_parameters']['virtual_host'],
        config['credentials']['username'],
        config['credentials']['password'],
        config['queue_bind']['exchange'],
        config['SMTP_HOST'],
    )
    worker.start()

def send(config, messagebody, count=1):
    """
    Send a test email message to workers.
    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host = config['connection_parameters']['host'],
            virtual_host = config['connection_parameters']['virtual_host'],
            credentials = pika.PlainCredentials(
                username = config['credentials']['username'],
                password = config['credentials']['password'],
            )
        )
    )

    channel = connection.channel()

    for _ in range(count):
        channel.basic_publish(
            exchange = config['queue_bind']['exchange'],
            routing_key = config['queue_bind']['exchange'],
            body = json.dumps(messagebody),
        )


def main():
    """
    Pika email worker.
    """
    instancedir = Path(__file__).parent.parent / 'instance'
    parser = argparse.ArgumentParser(prog='emailworker', description=main.__doc__)

    parser.add_argument(
        '--config',
        default = instancedir / 'config.py',
        help = 'Worker config file. Default: %(default)s')

    parser.add_argument(
        '--rabbitmq-config',
        default = instancedir / 'rabbitmq.ini',
        help = 'RabbitMQ config file. Default: %(default)s')

    subparsers = parser.add_subparsers()

    start_parser = subparsers.add_parser('start', help='Start worker. (default)')
    start_parser.set_defaults(func=start_worker)

    send_parser = subparsers.add_parser('send', help='Send an email.')
    # Message from config argument
    send_parser.add_argument(
        '--message',
        default = instancedir / 'testemail.ini',
        help = 'Config file to get message body from. Default: %(default)s'
    )
    # Count option
    parameter = inspect.signature(send).parameters['count']
    send_parser.add_argument(
        '-C', '--count',
        metavar = 'N',
        default = parameter.default,
        type = type(parameter.default),
        help = 'Send %(metavar)s emails. Default: %(default)s')
    send_parser.set_defaults(func=send)

    args = parser.parse_args()

    if 'func' not in args:
        args.func = start_worker
    func = args.func
    # none of the funcs expect themselves as an argument
    del args.func

    # add messagebody attribute from file and remove message attribute.
    if 'message' in args:
        args.messagebody = ConfigParser()
        args.messagebody.read(args.message)
        args.messagebody = dict(args.messagebody['email'].items())
        del args.message
        print(args.messagebody)
        return

    # replace args.config with the object that the funcs expect and remove
    # rabbitmq_config that none of them expect, so that they get any of the
    # remaining args and kwargs.
    args.config = load_config(str(args.config), str(args.rabbitmq_config))
    del args.rabbitmq_config
    sys.exit(bind_and_call(func, vars(args)))

import argparse
import logging
import sys
from pathlib import Path

import pynssm.cli

from .config import Config
from .config import DefaultConfig
from .util import bind_and_call
from .util import stripkeys
from .worker import Worker

PROG = 'emailworker'

def startworker():
    """
    Configure and start `emailworker.Worker` instance.
    """
    config = Config()
    config.from_object(DefaultConfig)

    path = Path(__file__).parent.parent.absolute() / "instance" / "config.py"
    if path.exists():
        config.from_pyfile(path)

    logger = logging.getLogger('emailworker')
    if 'LOGGING_CONF_DICT' in config:
        logging.config.dictConfig(config['LOGGING_CONF_DICT'])
        logger.debug('dict config loaded')

    logger.debug('config: %r', config)
    worker = Worker(config['RABBITMQ_HOST'], config['SMTP_HOST'], config['QUEUE'])
    worker.start()

def main():
    """
    Email Worker.
    """
    parser = argparse.ArgumentParser(prog=PROG, description=main.__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers()
    service_group = subparsers.add_parser('service')

    pynssm.cli.add_pythonapp_nssm_parsers(
        Path(__file__).parent.parts[-1],
        service_group,
        'worker',
        'start',
        as_module=True,
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    worker_group = subparsers.add_parser('worker')
    subparser = worker_group.add_subparsers()
    subparser = subparser.add_parser('start')
    subparser.set_defaults(func=startworker)

    args = parser.parse_args()

    rv = bind_and_call(args.func, stripkeys(vars(args), 'func'))

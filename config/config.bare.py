from pathlib import Path

thisdir = Path(__file__).parent.absolute()

# Only uppercase names are imported

# Your SMTP Host
SMTP_HOST = None

# Example:
#LOGGING_CONF_DICT = {
#    'version': 1,
#    'formatters': {
#        'default': {
#            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
#        }
#    },
#    'handlers': {
#        'console': {
#            'class': 'logging.StreamHandler',
#        },
#        'rotatingfile': {
#            'class': 'logging.handlers.RotatingFileHandler',
#            'filename': thisdir / 'emailworker.log',
#            'mode': 'w',
#            'formatter': 'default',
#        }
#    },
#    'loggers': {
#        'emailworker': {
#            'handlers': ['console', 'rotatingfile'],
#            'level': 'DEBUG',
#        }
#    },
#}

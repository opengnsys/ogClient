import logging
import logging.config
import os

from src.utils.net import getifaddr

DEFAULT_LOGGING_LINUX = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'formatter.syslog': {
            '()': 'logging.Formatter',
            'format': 'ogClient: [{levelname}] - {message}',
            'style': '{',
        },
        'formatter.console': {
            '()': 'logging.Formatter',
            'format': '[{levelname}] - {message}',
            'style': '{',
        },
        'formatter.syslogtime': {
            '()': 'logging.Formatter',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '({asctime}) ogClient: [{levelname}] - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'formatter.console',
            'stream': 'ext://sys.stdout',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'formatter.syslog',
            'address': '/dev/log',
        },
        'samba': {
            'class': 'logging.FileHandler',
            'formatter': 'formatter.syslogtime',
            'filename': f'/opt/opengnsys/log/{getifaddr(os.getenv("DEVICE"))}.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['syslog', 'console'],
            'level': 'INFO',
        },
    }
}

DEFAULT_LOGGING_WIN = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'formatter.console': {
            '()': 'logging.Formatter',
            'format': 'ogClient: [{levelname}] - {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'formatter.console',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

def configure_logging(mode, level):
    """
    Receives a ogClient operating mode.

    Configures the default logger according to the operating mode.

    For example, in the case of running live mode it will activate
    logging to the expected samba shared log file ({ip}.txt.log).
    """
    if mode == 'windows':
        logconfig = DEFAULT_LOGGING_WIN
    else:
        logconfig = DEFAULT_LOGGING_LINUX

    if mode == 'live':
        logconfig['loggers']['']['handlers'].append('samba')

    logconfig['loggers']['']['level'] = level

    logging.config.dictConfig(logconfig)

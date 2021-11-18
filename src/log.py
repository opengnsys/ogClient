import logging
import logging.config

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
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'formatter.console',
            'stream': 'ext://sys.stdout',
        },
        'syslog': {
            'level': 'DEBUG',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'formatter.syslog',
            'address': '/dev/log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['syslog', 'console'],
            'level': 'DEBUG',
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

def configure_logging(mode):
    if mode == 'windows':
        DEFAULT_LOGGING = DEFAULT_LOGGING_WIN
    else:
        DEFAULT_LOGGING = DEFAULT_LOGGING_LINUX
    logging.config.dictConfig(DEFAULT_LOGGING)

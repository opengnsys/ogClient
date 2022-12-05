import logging
import logging.config
import os


def _default_logging_linux():
    from src.utils.net import getifaddr
    logconfig = {
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
        },
        'loggers': {
            '': {
                'handlers': ['syslog', 'console'],
                'level': 'INFO',
            },
        }
    }
    return logconfig


def _default_logging_live():
    from src.utils.net import getifaddr
    logconfig = _default_logging_linux()
    samba = {
            'samba': {
                'class': 'logging.FileHandler',
                'formatter': 'formatter.syslogtime',
                'filename': f'/opt/opengnsys/log/{getifaddr(os.getenv("DEVICE"))}.log',
            }
        }
    rtlog = {
            'rtlog': {
                'class': 'logging.FileHandler',
                'formatter': 'formatter.syslogtime',
                'filename': f'/tmp/session.log',
            }
        }
    logconfig['handlers'].update(samba)
    logconfig['handlers'].update(rtlog)
    logconfig['loggers']['']['handlers'].append('samba')
    logconfig['loggers']['']['handlers'].append('rtlog')
    return logconfig


def _default_logging_win():
    logconfig = {
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
    return logconfig


def configure_logging(mode, level):
    """
    Receives a ogClient operating mode.

    Configures the default logger according to the operating mode.

    For example, in the case of running live mode it will activate
    logging to the expected samba shared log file ({ip}.txt.log).
    """
    if mode == 'windows':
        logconfig = _default_logging_win()
    elif mode == 'linux':
        logconfig = _default_logging_linux()
    elif mode == 'live':
        logconfig = _default_logging_live()
    else:
        raise ValueError(f'Error: Mode {mode} not supported')

    logconfig['loggers']['']['level'] = level

    logging.config.dictConfig(logconfig)

#
# Copyright (C) 2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import logging

from src.virtual.qmp import QEMUMonitorProtocol
from src.virtual.qmp import QMPCapabilitiesError, QMPConnectError

QMP_DEFAULT_PORT = 4445
QMP_DEFAULT_HOST = "127.0.0.1"

def is_shutdown_event(qmp_ev):
    """
    """
    return qmp_ev.get('event') == 'SHUTDOWN'


def init(host=QMP_DEFAULT_HOST, port=QMP_DEFAULT_PORT):
    """
    """
    qmpconn = QEMUMonitorProtocol((host, port))
    try:
        qmpconn.connect()
    except ConnectionRefusedError:
        logging.critical('poweroffd: Connection refused')
        return None
    except QMPCapabilitiesError as e:
        logging.critical('poweroffd: Error negotiating capabilities')
        return None
    return qmpconn


def run(qmpconn):
    """
    """
    while(True):
        try:
            qmp_ev = qmpconn.pull_event(wait=True)
        except QMPConnectError as e:
            logging.critical('Error trying to pull an event')
            ret = -1
            break
        if is_shutdown_event(qmp_ev):
            logging.info('Detected guest shutdown, powering off')
            ret = 0
            break

    qmpconn.close()
    return ret

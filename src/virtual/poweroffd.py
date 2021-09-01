#
# Copyright (C) 2021 Soleta Networks <info@soleta.eu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.


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
        print("Critical err: Connection refused")
        return None
    except QMPCapabilitiesError as e:
        print("Error negotiating capabilities")
        return None
    return qmpconn


def run(qmpconn):
    """
    """
    while(True):
        try:
            qmp_ev = qmpconn.pull_event(wait=True)
        except QMPConnectError as e:
            print("Error trying to pull an event")
            ret = -1
            break
        if is_shutdown_event(qmp_ev):
            print("Detected guest shutdown, let's go")
            ret = 0
            break

    qmpconn.close()
    return ret

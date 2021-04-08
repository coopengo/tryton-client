# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import http.client
import logging
import socket
import ssl
import os
try:
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

from functools import partial

from tryton import bus, device_cookie
from tryton.jsonrpc import ServerProxy, ServerPool, Fault
from tryton.fingerprints import Fingerprints
from tryton.config import get_config_dir
from tryton.exceptions import TrytonServerError, TrytonServerUnavailable
from tryton.config import CONFIG

CONNECTION = None
_USER = None
_USERNAME = ''
_HOST = ''
_PORT = None
_CLIENT_DATE = None
_DATABASE = ''
CONTEXT = {}
_VIEW_CACHE = {}
_TOOLBAR_CACHE = {}
_KEYWORD_CACHE = {}
_CA_CERTS = os.path.join(get_config_dir(), 'ca_certs')
if not os.path.isfile(_CA_CERTS):
    _CA_CERTS = None
_FINGERPRINTS = Fingerprints()

ServerProxy = partial(ServerProxy, fingerprints=_FINGERPRINTS,
    ca_certs=_CA_CERTS)
ServerPool = partial(ServerPool, fingerprints=_FINGERPRINTS,
    ca_certs=_CA_CERTS)


def context_reset():
    CONTEXT.clear()
    CONTEXT['client'] = bus.ID


context_reset()


def db_list(host, port):
    try:
        connection = ServerProxy(host, port)
        logging.getLogger(__name__).info('common.db.list()')
        result = connection.common.db.list()
        logging.getLogger(__name__).debug(repr(result))
        return result
    except Fault as exception:
        logging.getLogger(__name__).debug(exception.faultCode)
        if exception.faultCode == str(HTTPStatus.FORBIDDEN.value):
            return []
        else:
            return None


def server_version(host, port):
    try:
        connection = ServerProxy(host, port)
        logging.getLogger(__name__).info(
            'common.server.version(None, None)')
        result = connection.common.server.version()
        logging.getLogger(__name__).debug(repr(result))
        return result
    except (Fault, socket.error, ssl.SSLError, ssl.CertificateError) as e:
        logging.getLogger(__name__).error(e)
        return None


# ABD: Add date and set_date parameters to login function (ca093423)
def login(parameters):
    from tryton import common
    global CONNECTION, _USER
    global _CLIENT_DATE
    host = CONFIG['login.host']
    hostname = common.get_hostname(host)
    port = common.get_port(host)
    database = CONFIG['login.db']
    username = CONFIG['login.login']
    language = CONFIG['client.lang']
    date = CONFIG['login.date']
    parameters['device_cookie'] = device_cookie.get()
    connection = ServerProxy(hostname, port, database)
    logging.getLogger(__name__).info('common.db.login(%s, %s, %s)'
        % (username, 'x' * 10, language))
    result = connection.common.db.login(username, parameters, language)
    logging.getLogger(__name__).debug(repr(result))
    _USER = result[0]
    session = ':'.join(map(str, [username] + result))
    if CONNECTION is not None:
        CONNECTION.close()
    CONNECTION = ServerPool(
        hostname, port, database, session=session, cache=not CONFIG['dev'])
    _CLIENT_DATE = date
    device_cookie.renew()
    bus.listen(CONNECTION)


def logout():
    global CONNECTION, _USER
    global _CLIENT_DATE
    if CONNECTION is not None:
        try:
            logging.getLogger(__name__).info('common.db.logout()')
            with CONNECTION() as conn:
                conn.common.db.logout()
        except (Fault, socket.error, http.client.CannotSendRequest):
            pass
        CONNECTION.close()
        CONNECTION = None
    _CLIENT_DATE = None
    _USER = None


def _execute(blocking, *args):
    global CONNECTION, _USER
    if CONNECTION is None:
        raise TrytonServerError('403')
    try:
        name = '.'.join(args[:3])
        args = args[3:]
        logging.getLogger(__name__).info('%s%s' % (name, args))
        with CONNECTION() as conn:
            result = getattr(conn, name)(*args)
    except (http.client.CannotSendRequest, socket.error) as exception:
        raise TrytonServerUnavailable(*exception.args)
    logging.getLogger(__name__).debug(repr(result))
    return result


def execute(*args):
    return _execute(True, *args)


def execute_nonblocking(*args):
    return _execute(False, *args)


def clear_cache(prefix=None):
    if CONNECTION:
        CONNECTION.clear_cache(prefix)

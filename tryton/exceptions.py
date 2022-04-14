# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from .jsonrpc import Fault, ProtocolError

TrytonServerError = Fault
TrytonAuthenticationError = ProtocolError


class TrytonServerUnavailable(Exception):
    pass


class TrytonError(Exception):

    def __init__(self, faultCode):
        self.faultCode = faultCode

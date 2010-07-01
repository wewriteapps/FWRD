__author__ = 'Phillip B Oldham'
__version__ = '0.2.0-dev'
__licence__ = 'MIT'

import os
import re
import sys
import threading

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

try: 
    from simplejson import dumps as json_dumps
except ImportError:
    try:
        from json import dumps as json_dumps
    except ImportError:
        json_dumps = None

# http://www.faqs.org/rfcs/rfc2616.html
HTTP_STATUS_CODES = {
    100: "Continue", 
    101: "Switching Protocols", 
    200: "OK", 
    201: "Created", 
    202: "Accepted", 
    203: "Non-Authoritative Information", 
    204: "No Content", 
    205: "Reset Content", 
    206: "Partial Content", 
    300: "Multiple Choices", 
    301: "Moved Permanently", 
    302: "Found", 
    303: "See Other", 
    304: "Not Modified", 
    305: "Use Proxy", 
    307: "Temporary Redirect", 
    400: "Bad Request", 
    401: "Unauthorized", 
    402: "Payment Required", 
    403: "Forbidden", 
    404: "Not Found", 
    405: "Method Not Allowed", 
    406: "Not Acceptable",
    407: "Proxy Authentication Required", 
    408: "Request Time-out", 
    409: "Conflict", 
    410: "Gone", 
    411: "Length Required", 
    412: "Precondition Failed", 
    413: "Request Entity Too Large", 
    414: "Request-URI Too Large", 
    415: "Unsupported Media Type", 
    416: "Requested range not satisfiable", 
    417: "Expectation Failed", 
    500: "Internal Server Error", 
    501: "Not Implemented", 
    502: "Bad Gateway", 
    503: "Service Unavailable", 
    504: "Gateway Time-out", 
    505: "HTTP Version not supported",
    }

class HTTPServerError(Exception):
    pass

class InternalError(HTTPServerError):
    pass


class HTTPClientError(Exception):
    pass

class NotFound(HTTPClientError):
    pass

class Forbidden(HTTPClientError):
    pass


class HTTPRedirection(Exception):
    pass

class NotModified(HTTPRedirection):
    pass

class Redirect(HTTPRedirection):
    pass

class Moved(HTTPRedirection):
    pass

class Found(HTTPRedirection):
    pass

class SeeOther(HTTPRedirection):
    pass


class Config(object):
    pass

class Application(object):
    pass

class Route(object):
    pass

class Request(threading.local):
    pass

class Response(threading.local):
    pass

class TranslatedResponse(Response):
    '''Takes the response data and formats it first
    into XML then passes it through an XSL translator'''

    extensions = ('', 'html')
    contenttype = ''


class TextResonse(Response):
    '''Takes the response data and formats it into
    a text representation'''

    extensions = ('txt', 'text')
    contenttype = 'text/plain'

class XMLResponse(Response):
    '''Takes the response data and converts it into
    a "generic" XML representation'''

    extensions = ('xml')
    contenttype = 'application/xml'

class JSONResponse(Response):
    '''Takes the response data and converts it into
    a "generic" JSON representation'''

    extensions = ('json')
    contenttype = 'application/json'

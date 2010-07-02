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
    def __init__(self, url=None, method='GET'):
        if url: self.url = url 
        if method: self.method = method

    def __repr__(self):
        if self.url:
            message = 'routing failed when searching for %s' % self.url
            if self.method:
                message += ' using method %s' % self.method
            return message

    def __str__(self):
        return self.__repr__()

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

class RouteCompilationError(Exception):
    pass

class Route(object):

    __slots__ = [
        'HEAD',
        'GET',
        'POST',
        'PUT',
        'DELETE',
        ]

    _compile_patterns = (
        (r'\[', r'('),
        (r'\]', r')?'),
        (r'(?<!\\)_', r'[\s_]'),
        (r'\\_', r'_'),
        (r'\s+', r'\s+'),
        (r'(%)', r'\w'),
        (r'(\*)', r'\w+'),
        (r'([$!])', r'\\\1'),
        (r'(?<!\\):(\w+)', r'(?P<\1>[^/]+)'),
        )

    _route_tests = (
        (r'(\/\w+)?(\/?\[\/?:[\w]+\]){2,}','Consecutive conditional parameters are not allowed'),
        (r'\/\[\/', r'Syntax error: "/[/" not allowed'),
        (r'(?<![\[\/-\\]):', r'Constant/keyword mix not allowed without a valid separator: "/", or "-"'),
        (r'(\|.+)$', r'Partial route contains noise after break'),
        )

    _pattern_tests = (
        #('',''),
        )

    def __init__(self, urls=None):
        for method in self.__slots__:
            self[method] = []

        if urls:
            self._define_routes(urls)


    def __call__(self, *args, **kwargs):
        return self.find(*args, **kwargs)


    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def _define_routes(self, urls, prefix=''):
        for item in urls:
            if not isinstance(item, tuple):
                break
            
            item = dict(zip(['regex', 'func', 'methods'], item))

            self._define_methods(item)
            self._define_route(item, prefix=prefix)


    def _define_methods(self, item):
        if not 'methods' in item:
            item['methods'] = ['GET']
            return

        item['methods'] = [method.upper() for method in re.split('\W+', item['methods']) if method.upper() in self.__slots__]


    def _define_route(self, item, prefix=''):
        if type(item['func']) is tuple:
            self._define_routes(item['func'], prefix=item['pattern'])

        else: # hasattr(item['match'], '__call__'):
            for method in item['methods']:
                pattern, regex = self._compile(item['route'], prefix=prefix)
                self[method].append((item['route'], regex, pattern, item['func']))
            

    def _compile(self, pattern, prefix=''):
        if str(pattern[0]) is '^':
            regex = r'^' + prefix + pattern[1:]

        else:
            regex = prefix + pattern

            for test, reason in self._route_tests:
                if re.search(test, regex):
                    reason += "\n  while testing %s" % regex
                    raise RouteCompilationError(reason)

            for search, replace in self._compile_patterns:
                regex = re.sub(search, replace, regex)
                
            if pattern[-1] is '|':
                regex = r'^' + regex[:-1]
            else:
                regex = r'^' + regex + r'$'

        for test, reason in self._pattern_tests:
            if re.search(test, regex):
                reason += "\n  while testing %s" % regex
                raise RouteCompilationError(reason)
        
        try:
            return re.compile(regex), regex
            
        except Exception as e:
            raise RouteCompilationError(e.message+' while testing: %s' % regex)


    def _get_all(self):
        return dict( (item, getattr(self, item)) for item in self.__slots__ )


    def find(self, method, url):

        if len(url) > 1 and url[-1] == '/':
            url = url[0:-1]

        for route, regex, test, func in self[method]:
            match = test.match(url)
            if match:
                return func, match.groupdict(), route

        raise NotFound(url=url, method=method)


    def add(self, route, func, methods='GET', prefix=''):
        item = {'route':route, 'func':func, 'methods':methods}
        self._define_methods(item)
        self._define_route(item, prefix)

    # Properties
    urls = property(_get_all, __init__)


class RequestHeaders(threading.local):
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

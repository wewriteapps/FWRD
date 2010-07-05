__author__ = 'Phillip B Oldham'
__version__ = '0.2.0-dev'
__licence__ = 'MIT'

import cgi
import os
import re
import sys
import threading
from wsgiref.headers import Headers as WSGIHeaderObject

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

try:
    try:
        import simplejson as json
    except:
        import json
except ImportError:
    json = None

try:
    from collections import MutableMapping as DictMixin
except ImportError:
    from UserDict import DictMixin

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
    __slots__ = [
        'host',
        'port'
        ]

    def __init__(self, **kwargs):
        self.host = ''
        self.port = 8000

        for key, value in kwargs.iteritems():
            if key.lower() in self.__slots__:
                setattr(self, key.lower(), value)


class Application(threading.local):
    __slots__ = [
        'router',
        'request',
        'response',
        'middleware'
        ]

    def __init__(self, router, *args, **kwargs):
        self.router = router
        self.middleware = []

    def __call__(self, environ, start_response):
        self.request = Request(environ)
        self.response = ResponseFactory.new(self.request.path[2], start_response)

        return self.process_request()

    def process_request(self):
        func, params, route = self.router.find(request.path[1])

        try:
            try:
                headers = {}
                code = 200
                body = None
                
                if func:
                    body = method(**self.request.params)

            except TypeError as e:
                if 'unexpected keyword argument' in str(e):
                    raise Forbidden('%s received unexpected parameter "%s"' % (func.__name__, str(e).split(' ')[-1]))

                if 'takes no arguments' in str(e):
                    raise Forbidden('method '+' '.join(str(e).split(' ')[1:]))

                raise e

            except Exception as e:
                raise e

        except (KeyboardInterrupt, SystemExit) as e:
            print >>config.output, "Terminating."

        except HTTPRedirection as e:
            code = e.code
            headers = e.headers
            body = None

        except Conflict as e:
            code = e.code
            headers = e.headers
            body = e

        except HTTPClientError as e:
            code = e.code
            headers = e.headers
            body = e

        except HTTPServerError as e:
            code = e.code
            headers = e.headers
            body = e

        except Exception as e:
            raise e

        finally:
            return self.response(body, code=code, additional_headers=headers)

    def register_middleware(self, middleware, opts={}):
        self.middleware.append((middleware, opts))

    def run(self, server_func=None, host=None, port=None, **kwargs):

        if server_func is None:
            server_func = self._serve_once

        if not host:
            host = config.host

        if not port:
            port = config.port

        server_func(
            reduce(
                lambda stack, middleware: middleware[0](stack, **middleware[1]),
                self.middleware,
                self
                ),
            host,
            port,
            **kwargs
            )

    def _serve_once(self, app, host, port):
        from wsgiref.simple_server import make_server
        server = make_server(host, port, app)
        server.handle_request()

    def _serve_forever(self, app, host, port):
        from wsgiref.simple_server import make_server
        server = make_server(host, port, app)
        server.serve_forever()


class RouteCompilationError(Exception):
    pass

class Route(threading.local):

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


class HeaderContainer(threading.local):
    __slots__ = [
        'headers'
        ]

    def __init__(self, *args, **kwargs):
        self.headers = WSGIHeaderObject([])
        for key, value in dict(*args, **kwargs).iteritems():
            self.add_header(key, value)

    def __call__(self):
        return str(self.headers)

    def __len__(self):
        return len(set(self.headers.keys()))

    def __setitem__(self, name, value):
        self.add(name, value)

    def __getitem__(self, name):
        return self.headers[name]

    def __contains__(self, name):
        return name in self.headers

    def __delitem__(self, name):
        del self.headers[name]

    def __repr__(self):
        return str(self.headers)

    def get(self, name):
        return self.headers[name]

    def get_all(self, name):
        return self.headers.get_all(name)

    def keys(self):
        return self.headers.keys()

    def values(self):
        return self.headers.values()

    def items(self):
        return self.headers.items()

    def has_key(self, name):
        return self.headers.has_key(name)

    def list(self):
        return self.headers.items()

    def add(self, name, value, **params):
        self.add_header(name, value, **params)

    def add_header(self, name, value, **params):
        self.headers.add_header(name.replace('_', '-').title(), str(value), **params)

    def clear(self):
        self.headers = WSGIHeaderObject([])

    def drop(self, name):
        del self.headers[name]


class Request(threading.local):
    ''' Should a factory be used to create a request/response obj per "request"?'''
    __slots__ = [
        'GET',
        'PATH',
        'POST',
        'PUT',

        'environ',
        'method',
        'path',
        'param_order',
        ]

    _get_ext = re.compile(r'^(.+)(\.[a-z]+)$')
    _is_float = re.compile(r'\d+\.\d+')
    _is_named = re.compile(r'^(\w+)(\[.+\])$')

    def __init__(self, environ=None, **kwargs):
        self.environ = environ
        self.method = environ['REQUEST_METHOD'].upper()

        self.path = (environ['PATH_INFO'], '', environ['PATH_INFO'])

        try:
            self.path = tuple(list(self._get_ext.match(environ['PATH_INFO'])).append(environ['PATH_INFO']))
        except:
            pass

        if param_order in kwargs:
            self.param_order = tuple(param_order.split(','))
        else:
            self.param_order = ('SESSION','PATH','GET','POST')

        if len(self.environ['QUERY_STRING']):
            self.parse_qs()

        if self.method in ('POST', 'PUT'):
            self.parse_body()

        def parse_qs(self):
            self.GET = self.parse_parameters(parse_qs(self.environ['QUERY_STRING']))

        def parse_body(self):
            if self.environ.get('CONTENT_TYPE', '').lower()[:10] == 'multipart/':
                fp = self.environ['wsgi.input']

            else:
                length = int(self.environ.get('CONTENT_LENGTH', 0) or 0)
                fp = StringIO(self.environ['wsgi.input'].read(length))

            self.POST = self.parse_parameters(cgi.FieldStroage(fp=fp,
                                                               environ=self.environ,
                                                               keep_blank_values=True))

        def parse_parameters(self, params):
            parsed = {}

            self.parse_sequenced_parameters(params, parsed)
            self.parse_named_parameters(params, parsed)
            self.parse_basic_parameters(params, parsed)

            return parsed
                      

        def parse_sequenced_parameters(self, params, parsed={}):
            parsed = {}

            sequenced = [name[:-2] for name in params if name[-2:] == '[]']

            for item in sequenced:
                items = params.pop(item+'[]')

                '''Catch cases where a param is assigned multiple
                times in a querystring, such as:
                foo=bar&foo[]=baz&foo[]=false
                '''
                if item in params:
                    items.extend(params.pop(item))

                values = [self.update_param_type(value) for value in items]
                parsed[item] = dict(zip(range(0, len(values)), list(values)))

            return parsed

        def parse_named_parameters(self, params, parsed={}):

            named = [name for name in params if self._is_named.search(name)]

            for item in named:
                matches = self._is_named.match(item)
                name = matches[0]
                value = self.update_param_type(params[item])

                if name not in parsed:
                    parsed[name] = {}

                trie = [self.update_param_type(item) for item in matches.groups()[1][1:-1].split('][')]

                if type(parsed[name]) is not dict:
                    params[name] = {'_': params[name]}

                params[key].update(self.build_dict(trie, value))

            return parsed

        def parse_basic_parameters(self, params, parsed={}):

            for name, value in params.iteritems():
                parsed[name] = self.update_param_type(value)

            return parsed

        def build_dict(self, sequence, value):
            if len(sequence) == 1:
                return {
                    sequence[0]: value
                    }

            return {
                sequence.pop(0): self.build_dict(sequence, value)
                }

        def update_param_type(self, param):
            if isinstance(param, cgi.MiniFieldStorage):
                return param.value

            if type(param) is list and len(param) == 1:
                return self.update_param_type(param[0])

            if type(param) is list:
                return list(self.update_param_type(item) for item in param)

            if self._is_float.match(param):
                return float(param)

            if param != '' and param[0] is not '0' and param.isdigit():
                return int(param)

            if param == '':
                return None

            if param.lower() == 'true':
                return True

            if param.lower() == 'false':
                return False

            return param

        def build_get_string(self):
            return self.build_qs(self.GET)

        def build_post_string(self):
            return self.build_qs(self.POST)

        def build_qs(self, params, key=None):
            parts = []

            if params and hasattr(params, 'items'):
                for name, value in param.items():

                    if hasattr(value, 'values'):
                        '''Encode a dict'''
                        parts.extend(self.build_qs(params=value.values(),
                                                   key=self.build_qs_key(key, cgi.escape(name))))

                    elif hasattr(value, '__iter__'):
                        '''Encode an iterable (list, tuple, etc)'''
                        parts.extend(self.build_qs(params=dict(zip(range(0, len(value)), value)),
                                                   key=self.build_qs_key(key, cgi.escape(name))))

                    else:
                        parts.extend('%s=%s' % (self.build_qs_key(key, cgi.escape(name)), cgi.escape(str(value))))

            return '&'.join(parts)
                        
        def build_qs_key(self, key, addition):
            if not key:
                return addition

            return '%s[%s]' % (key, addition)

        @property
        def params(self):
            params = {}

            for item in self.param_order:
                params.update(getattr(self, item))

            return params
        

class PluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []

        else:
            cls.plugins.append(cls)


class Response(threading.local):
    __metaclass__ = PluginMount

    def __init__(self, start_response, *args, **kwargs):
        self.start_response = start_response
        self.headers = HeaderContainer()

    def __call__(self, response_body, code=200, additional_headers=None):
        self.response_body = response_body
        self.headers.update(additional_headers)

        self.start_response(code, self.headers.list())
        return self.format(self.response_body)

    def format(self, *args, **kwargs):
        raise NotImplementedError()

class InvalidResponseTypeError(Exception):
    pass

class ResponseTranslationError(Exception):
    pass

class ResponseFactory(object):
    @staticmethod
    def new(response_type=None, *args, **kwargs):
        if response_type:
            response_type = response_type.lower()
        for response_class in Response.plugins:
            if hasattr(response_class, 'extension') and response_type == response_class.extension:
                return response_class(*args, **kwargs)

            if hasattr(response_class, 'extensions') and response_type in response_class.extensions:
                return response_class(*args, **kwargs)

        return TranslatedResponse(*args, **kwargs)
        #raise InvalidResponseTypeError()


class TranslatedResponse(Response):
    '''Takes the response data and formats it first
    into XML then passes it through an XSL translator'''

    extensions = (None, '', 'htm', 'html')
    contenttype = ''


class TextResponse(Response):
    '''Takes the response data and formats it into
    a text representation'''

    extensions = ('txt', 'text')
    contenttype = 'text/plain'

    def format(self, data=None):
        if not data and not self.response_body:
            return ''

        if not data and self.response_body:
            data = self.response_body

        if isinstance(data, basestring):
            return str(data)

        raise ResponseTranslationError
    

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

    def format(self, data=None):
        if data is None and not self.response_body:
            return ''

        if data is None and self.response_body:
            data = self.response_body

        return json.dumps(
            data,
            sort_keys=True,
            separators=(',',':'),
            cls=ComplexJSONEncoder
            )



'Utility JSON methods'

class ComplexJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '__iter__'):
            return list(obj)

        if hasattr(obj, 'isoformat'):
            return obj.isoformat()

        if isinstance(obj, object):
            newobj = {}

            # class attributes
            newobj.update(dict(
                (name, value)
                for name, value
                in dict(obj.__class__.__dict__).iteritems()
                if name[0] != '_'
                ))

            # object attributes
            newobj.update(dict(
                (name, value)
                for name, value
                in obj.__dict__.iteritems()
                if ord(name[0].lower()) in range(97,123)
                ))

            newobj['__name__'] = obj.__class__.__name__

            return newobj

        return json.JSONEncoder.default(self, obj)
         

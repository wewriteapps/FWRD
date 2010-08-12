__author__ = 'Phillip B Oldham'
__version__ = '0.2.0-dev'
__licence__ = 'MIT'

import cgi
import collections
import copy
import functools
import inspect
import iso8601
import os
import re
import sys
import threading
import traceback
import xml.parsers.expat
from datetime import datetime
from lxml import etree
from urllib import unquote as urlunquote
from uuid import UUID
from wsgiref.headers import Headers as WSGIHeaderObject
from xml.sax.saxutils import escape

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


__all__ = [
    'application',
    'config',
    'router',
    'request',
    'response',

    # Common "exceptions"
    'Moved',         # 301
    'Found',         # 302
    'SeeOther',      # 303
    'NotModified',   # 304
    'Redirect',      # 307
    'Forbidden',     # 403
    'NotFound',      # 404
    'InternalError', # 500
    ]


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

class HTTPError(Exception):
    code = 500
    headers = {}
    _message = 'an unexpected error has occurred'

    def _get_message(self):
        return self._message

    def _set_message(self, message):
        self._message = message

    def __repr__(self):
        return '<HTTPException "%s">' % self.__str__()
    
    def __str__(self):
        return '%d %s: %s' % (self.code, HTTP_STATUS_CODES[self.code], self._message)

    message = property(_get_message, _set_message)

class HTTPServerError(HTTPError):
    pass

class InternalError(HTTPServerError):
    pass


class HTTPClientError(HTTPError):
    code = 400

class NotFound(HTTPClientError):
    code = 404
    def __init__(self, url=None, method='GET'):
        if url:
            self.url = url 
        if method:
            self.method = method

        self.message = str(self)

    def __repr__(self):
        if self.url:
            message = 'routing failed when searching for "%s"' % self.url
            if self.method:
                message += ' using method %s' % self.method
            return message

    def __str__(self):
        return self.__repr__()

class Forbidden(HTTPClientError):
    code = 403

    def __init__(self, message, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.message = message


class HTTPRedirection(HTTPError):
    code = 300
    def __init__(self, location):
        self.headers = HeaderContainer()
        self.headers['location'] = location
        self.message = ''

class NotModified(HTTPRedirection):
    code = 304
    def __init__(self):
        """Not Modified doesn't issue a Location header"""
        self.headers = HeaderContainer()

class Redirect(HTTPRedirection):
    code = 307

class Moved(HTTPRedirection):
    code = 301

class Found(HTTPRedirection):
    code = 302

class SeeOther(HTTPRedirection):
    code = 303


class Config(threading.local):
    __slots__ = [
        'host',
        'port',
        'format',
        'output',
        'app_path',
        'default_format',
        ]

    def __init__(self, **kwargs):
        self.host = ''
        self.port = 8000
        self.format = {}
        self.default_format = None
        self.output = sys.stdout

        for key, value in kwargs.iteritems():
            if key.lower() in self.__slots__:
                setattr(self, key.lower(), value)


class Application(threading.local):
    __slots__ = [
        '_config',
        '_router',
        '_request',
        '_response',
        '_middleware'
        ]

    def __init__(self, config, router, *args, **kwargs):
        self._config = config
        self._router = router
        self._middleware = []

    def __call__(self, environ, start_response):
        self._request = Request(environ)
        try:
            self._response = ResponseFactory.new(self._request.path[1], start_response, self._request, self._config.format)
        except InvalidResponseTypeError:
            self._response = ResponseFactory.new(self._config.default_format, start_response, self._request, self._config.format)

        return self.process_request()

    def _run_func(self):
        def __none__():
            pass

        func, path_params, self._request.route = self._router.find(self._request.method, self._request.path[0])

        self._request.set_path_params(path_params)
        
        if not func:
            func = __none__
            func.__name__ = 'None'
            
        argspec = inspect.getargspec(func)
        allows_kwargs = argspec.keywords != None
        expected_args = set(argspec.args)
        arg_defaults = argspec.defaults or tuple()
        req_params = set(self._request.params.keys())
        
        # skip the "self" arg for class methods
        if inspect.ismethod(func):
            expected_args = set(argspec.args[1:])
        
        non_default_args = set(list(expected_args)[:len(expected_args)-len(arg_defaults)])
        
        # check that the func will accept args
        if not allows_kwargs and not expected_args and req_params:
            raise Forbidden('method "%s" takes no arguments' % func.__name__)
        
        # check that all non-default args have matching params
        if non_default_args & req_params != non_default_args:
            raise Forbidden('method "%s" requires (%s), missing (%s)' %
                            (func.__name__, ', '.join(non_default_args), ', '.join(non_default_args ^ req_params)))
        
        # check that we don't have any extra params when we can't accept them (kwargs)
        if not allows_kwargs and expected_args ^ req_params:
            raise Forbidden('method "%s" received unexpected params: %s' % (func.__name__, ', '.join(expected_args ^ req_params)))
        
        return func(**self._request.params)
            
    def process_request(self):

        headers = {}
        code = 200
        body = None

        try:
            body = {
                'content': self._run_func(),
                'errors': self._response.errors,
                }
            
        except (KeyboardInterrupt, SystemExit) as e:
            print >>config.output, "Terminating."

        except HTTPRedirection as e:
            code = e.code
            headers = e.headers
            body = None

        except HTTPClientError as e:
            code = e.code
            headers = e.headers
            body = self._format_error(code, e)

        except HTTPServerError as e:
            code = e.code
            headers = e.headers
            body = self._format_error(code, e)

        except Exception as e:
            traceback.print_exc(file=config.output)
            code = 500
            body = self._format_error(code, e)
            raise e
            
        #finally:
        return self._response(body, code=code, additional_headers=headers)

    def register_middleware(self, middleware, opts={}):
        self._middleware.append((middleware, opts))

    def run(self, server_func=None, host=None, port=None, debug=False, **kwargs):

        if server_func is None and debug:
            server_func = self._serve_once

        elif server_func is None:
            server_func = self._serve_forever

        if not host:
            host = self._config.host

        if not port:
            port = self._config.port

        server_func(
            reduce(
                lambda stack, middleware: middleware[0](stack, **middleware[1]),
                self._middleware,
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

    def _format_error(self, code, error):
        return {
            '__error__': code,
            '__message__': error.message,
            '__http_method__': self._request.method.upper(),
            '__request_path__': self._request.path[2],
            }

    def _get_config(self):
        return self._config
        
    def _get_router(self):
        return self._router

    def _get_request(self):
        try:
            return self._request
        except AttributeError:
            pass

    def _get_response(self):
        try:
            return self._response
        except AttributeError:
            pass


    config    = property(_get_config)
    router    = property(_get_router)
    request   = property(_get_request)
    response  = property(_get_response)


class RouteCompilationError(Exception):
    pass

class Router(object):

    __slots__ = [
        'HEAD',
        'GET',
        'POST',
        'PUT',
        'DELETE',
        '_debug',
        ]

    _compile_patterns = (
        (r'\[', r'('),
        (r'\]', r')?'),
        (r'(?<!\\):(\w+)', r'(?P<\1>[^/]+)'),
        (r'(?<!\\)_', r'[\s_]'),
        (r'\\_', r'_'),
        (r'\s+', r'\s+'),
        (r'(%)', r'\w'),
        (r'(\*)', r'\w+'),
        (r'([$!])', r'\\\1'),
        (r'(\(\?P\<\w*)\[\\s_\](\w*\>)', r'\1_\2'), # fix parameters which contain underscores
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
            if method[0] != '_':
                self[method] = []

        self.debug = False

        if urls:
            self._set_urls(urls)


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
            
            item = dict(zip(['route', 'func', 'methods'], item))

            self._define_methods(item)
            self._define_route(item, prefix=prefix)


    def _define_methods(self, item):
        if not 'methods' in item:
            item['methods'] = ['GET']
            return

        item['methods'] = [method.upper() for method in re.split('\W+', item['methods']) if method.upper() in self.__slots__]


    def _define_route(self, item, prefix=''):
        if type(item['func']) is tuple:
            self._define_routes(item['func'], prefix=item['route'])

        else: #hasattr(item['func'], '__call__'):
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


    def _get_urls(self):
        return dict( (item, getattr(self, item)) for item in self.__slots__ )


    def _set_urls(self, urls=None):
        if urls:
            self._define_routes(urls)


    def _get_debug_mode(self):
        try:
            return self._debug
        except AttributeError:
            return False


    def _set_debug_mode(self, debugmode):
        if debugmode is not True:
            self._debug = False
        else:
            self._debug = True


    def find(self, method, url):

        if self.debug:
            return self.find_with_output(method, url)

        method = method.upper().strip()

        if len(url) > 1 and url[-1] == '/':
            url = url[0:-1]

        for route, regex, test, func in self[method]:
            match = test.search(url)
            if match:
                return (func, match.groupdict(), route)

        raise NotFound(url=url, method=method)


    def find_with_output(self, method, url):

        method = method.upper().strip()

        if len(url) > 1 and url[-1] == '/':
            url = url[0:-1]

        print "Finding url: %s" % url

        for route, regex, test, func in self[method]:
            print "  Testing %s" % regex
            match = test.search(url)
            if match:
                print "  Match found: %s > %s" % (route, regex)
                return (func, match.groupdict(), route)

        raise NotFound(url=url, method=method)


    def add(self, route, func, methods='GET', prefix=''):
        item = {'route':route, 'func':func, 'methods':methods}
        self._define_methods(item)
        self._define_route(item, prefix)

    # Properties
    urls = property(_get_urls, _set_urls)
    debug = property(_get_debug_mode, _set_debug_mode)


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

    def iteritems(self):
        for item in self.items():
            yield item

    def has_key(self, name):
        return self.headers.has_key(name)

    def list(self):
        return self.headers.items()

    def add(self, name, value, **params):
        self.add_header(name, value, **params)

    def add_header(self, name, value, **params):
        self.headers.add_header(name.replace('_', '-').title(), str(value), **params)

    def replace(self, name, value, **params):
        del self.headers[name]
        self.add_header(name, value, **params)

    def clear(self):
        self.headers = WSGIHeaderObject([])

    def drop(self, name):
        del self.headers[name]

    def update(self, items):
        for name, value in items.iteritems():
            self.add_header(name, value)


class Request(threading.local):
    ''' Should a factory be used to create a request/response obj per "request"?'''
    __slots__ = [

        # HTTP param containers
        'GET',
        'PATH',
        'POST',
        'PUT',
        'SESSION',

        # general parameters
        'environ',
        'method',
        'path',
        'route',
        'param_order',

        # properties
        'params',
        'session',
        
        ]

    _get_ext = re.compile(r'^(.+)\.([a-z]+)$')
    _is_float = re.compile(r'\d+\.\d+')
    _is_named = re.compile(r'^(\w+)(\[.+\])$')

    _default_env = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '',
        'QUERY_STRING': '',
        }

    def __init__(self, environ=None, **kwargs):

        for slot in [slot for slot in self.__slots__ if slot.isupper()]:
            setattr(self, slot, {})

        if 'param_order' in kwargs:
            self.param_order = tuple(param_order.split(','))
        else:
            self.param_order = ('PATH','GET','POST')

        if environ:
            self.environ = environ
        else:
            self.environ = self._default_env
            
        self.method = self.environ['REQUEST_METHOD'].upper()
        self.route = '__not_found__'
        self.path = (self.environ['PATH_INFO'], '', self.environ['PATH_INFO'])

        if 'beaker.session' in self.environ:
            self.SESSION = self.environ['beaker.session']

        try:
            self.path = tuple(
                list(self._get_ext.search(self.environ['PATH_INFO']).groups())
                +
                [self.environ['PATH_INFO']]
                )
        except:
            pass

        if len(self.environ['QUERY_STRING']):
            self.parse_qs()

        if self.method in ('POST', 'PUT'):
            self.parse_body()

    def __getitem__(self, name):
        return getattr(self, name, None)

    def set_path_params(self, params):
        self.PATH = dict((k, self.unquote(v)) for k, v in params.iteritems())

    def parse_qs(self):
        self.GET = self.parse_parameters(parse_qs(self.environ['QUERY_STRING']))

    def parse_body(self):
        if self.environ.get('CONTENT_TYPE', '').lower()[:10] == 'multipart/':
            fp = self.environ['wsgi.input']
            
        else:
            length = int(self.environ.get('CONTENT_LENGTH', 0) or 0)
            fp = StringIO(self.environ['wsgi.input'].read(length))
            
        self.POST = self.parse_parameters(cgi.FieldStorage(fp=fp,
                                                           environ=self.environ,
                                                           keep_blank_values=True))

    def parse_parameters(self, params):
        parsed = {}

        if hasattr(params, 'list'):
            params = self.simplify_params(params.list)

        self.parse_simple_parameters(params, parsed)
        self.parse_sequenced_parameters(params, parsed)
        self.parse_named_parameters(params, parsed)

        return parsed


    def simplify_params(self, params):
        simplified = {}

        for item in params:
            if item.name not in simplified:
                simplified[item.name] = []
            simplified[item.name].append(item.value)

        return simplified
                      

    def parse_sequenced_parameters(self, params, parsed={}):

        sequenced = dict([(name[:-2], self.update_param_type(value)) for name, value in params.iteritems() if name[-2:] == '[]'])

        for item, values in sequenced.iteritems():
            parsed[item] = dict(zip(xrange(0, len(values)), list(values)))

        return parsed
            
    def parse_named_parameters(self, params, parsed={}):

        named = [name for name in params if self._is_named.search(name)]

        for item in named:
            matches = self._is_named.search(item)
            name = matches.groups()[0]
            value = self.update_param_type(params[item])
            
            if name not in parsed:
                parsed[name] = {}
                
            trie = [self.update_param_type(item) for item in matches.groups()[1][1:-1].split('][')]

            if type(parsed[name]) is not dict:
                params[name] = {'_': params[name]}

            parsed[name].update(self.build_dict(trie, value))

        return parsed
    
    def parse_simple_parameters(self, params, parsed={}):

        simple = set([name for name in params if '[' not in name])
        indexed = set([name for name in params if '[' not in name and name+'[]' in params])

        for name in indexed:
            params[name+'[]'].extend(params[name])
            del params[name]

        for name in simple - indexed:
            parsed[name] = self.update_param_type(params[name])
        
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
        
        if param.strip() == '':
            return None
        
        if self._is_float.match(param):
            return float(param)
        
        if len(param) > 1 and param[0] is not '0' and param.isdigit():
            return int(param)

        if len(param) == 1 and param.isdigit():
            return int(param)
        
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
            for name, value in params.items():
                
                if hasattr(value, 'values'):
                    '''Encode a dict'''
                    parts.extend(self.build_qs(params=value.values(),
                                               key=self.build_qs_key(key, cgi.escape(name))))

                elif hasattr(value, '__iter__'):
                    '''Encode an iterable (list, tuple, etc)'''
                    parts.extend(self.build_qs(params=dict(zip(xrange(0, len(value)), value)),
                                               key=self.build_qs_key(key, cgi.escape(name))))
                    
                else:
                    parts.extend('%s=%s' % (self.build_qs_key(key, cgi.escape(name)), cgi.escape(str(value))))
                    
        return '&'.join(parts)
                        
    def build_qs_key(self, key, addition):
        if not key:
            return addition
        
        return '%s[%s]' % (key, addition)

    def unquote(self, value):
        if isinstance(value, basestring):
            return urlunquote(value)
        return value
    
    def get_params(self):
        params = {}
        
        for item in self.param_order:
            params.update(getattr(self, item, {}))
            
        return params

    def get_session(self):
        try:
            return self.SESSION
        except:
            return {}

    params = property(get_params)
    session = property(get_session)
    querystring = property(build_get_string)
    poststring = property(build_post_string)



class InvalidResponseTypeError(Exception):
    pass


class ResponseTranslationError(Exception):
    pass


class ResponseParameterError(Exception):
    pass


class PluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []

        else:
            cls.plugins.insert(0, cls)


class Response(threading.local):
    __metaclass__ = PluginMount

    start_response = None
    request = None
    config = None
    headers = None
    responsebody = None
    responsetype = None
    params = None
    errors = None

    def __init__(self, start_response, request, config={}, **kwargs):
        self.start_response = start_response
        self.request = request
        self.config = config

        self.headers = HeaderContainer(content_type=self.contenttype)
        self.params = {}
        self.errors = {}

        if kwargs:
            self._update_params(**kwargs)

    def _update_params(self, **kwargs):
        
        try:
            self.params.update(self.config[self.responsetype])
        except KeyError:
            pass

        self.params.update(kwargs)

    def __call__(self, responsebody, code=200, additional_headers=None, **kwargs):
        self.code = code
        self.responsebody = responsebody
        self.headers.update(additional_headers)
        output = self.format(self.responsebody, **kwargs)
        self.start_response(self.code, self.headers.list())
        return output.split("\n")

    def _set_code(self, code):
        self._code = code

    def _get_code(self):
        if not self._code:
            self._code = 200

        if not self._code in HTTP_STATUS_CODES:
            self._code = 500

        return "%d %s" % (self._code, HTTP_STATUS_CODES[self._code])

    def set_error(self, name, value):
        self.errors[name] = value

    def format(self, *args, **kwargs):
        raise NotImplementedError()

    code = property(_get_code, _set_code)


class ResponseFactory(threading.local):
    @staticmethod
    def new(response_type=None, *args, **kwargs):
        if response_type:
            response_type = response_type.lower()

        for response_class in Response.plugins:
            if hasattr(response_class, 'extensions') and response_type in tuple(response_class.extensions):
                return response_class(*args, **kwargs)

        raise InvalidResponseTypeError()


class TranslatedResponse(Response):
    '''Takes the response data and formats it first
    into XML then passes it through an XSL translator'''

    responsetype = 'xsl'
    extensions = (None, '', 'htm', 'html')
    contenttype = ''

    def __init__(self, start_response, request, config={}, **kwargs):
        super(self.__class__, self).__init__(start_response, request, config=config)
        self.params['stylesheet_path'] = None
        self.params['default_stylesheet'] = None
        self._update_params(**kwargs)

    def format(self, data=None, **kwargs):

        if 'stylesheet_path' not in self.params or not self.params['stylesheet_path']:
            raise ResponseParameterError("the stylesheet path must be set")

        if not os.path.isdir(os.path.abspath(self.params['stylesheet_path'])):
            raise ResponseParameterError("the stylesheet path is invalid")

        self.params['stylesheet_path'] = os.path.abspath(self.params['stylesheet_path'])

        if 'default_stylesheet' not in self.params or not self.params['default_stylesheet']:
            raise ResponseParameterError("the default stylesheet filename must be set")

        if not os.path.isfile(os.path.join(self.params['stylesheet_path'], self.params['default_stylesheet'])):
            raise ResponseParameterError('the default stylesheet could not be found')

        xslfile = os.path.join(self.params['stylesheet_path'], self.params['default_stylesheet'])

        xml = XMLEncoder(
            data,
            doc_el='response',
            encoding='UTF-8',
            request=self.request.path[0],
            route=self.request.route,
            method=self.request.method.lower()
            ).to_string()
     
        xsl = XSLTranslator(None,
                            xslfile,
                            path=self.params['stylesheet_path'],
                            extensions=[XPathCallbacks],
                            params={
                                'request': self.request,
                                },
                            resolvers=[LocalFileResolver(self.params['stylesheet_path'])]
                            )

        self.headers.replace('Content-Type', xsl.contenttype)

        return xsl.to_string(xml=xml)


class TextResponse(Response):
    '''Takes the response data and formats it into
    a text representation'''

    extensions = ('txt', 'text')
    contenttype = 'text/plain'

    def format(self, data=None):
        if not data and not self.responsebody:
            return ''

        if not data and self.responsebody:
            data = self.responsebody

        if isinstance(data, basestring):
            return str(data)

        raise ResponseTranslationError
    

class XMLResponse(Response):
    '''Takes the response data and converts it into
    a "generic" XML representation'''

    extensions = ('xml',)
    contenttype = 'application/xml'

    def format(self, data=None):
            
        return XMLEncoder(
            data,
            doc_el='response',
            encoding='UTF-8',
            request=self.request.path[0],
            route=self.request.route,
            method=self.request.method.lower()
            ).to_string()


class JSONResponse(Response):
    '''Takes the response data and converts it into
    a "generic" JSON representation'''

    extensions = ('json',)
    contenttype = 'application/json'

    def format(self, data=None):
        if data is None and not self.responsebody:
            return '{}'

        if data is None and self.responsebody:
            data = self.responsebody

        return json.dumps(
            data,
            sort_keys=True,
            separators=(',',':'),
            cls=ComplexJSONEncoder
            )

        try:
            pass
        except Exception as e:
            raise ResponseTranslationError(e)


class PropertyProxy(object):
    __slots__ = [
        '_property'
        ]
    def __init__(self, prop):
        object.__setattr__(self, '_property', prop)

    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, '_property')(), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, '_property')(), name, value)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, '_property')(), name)

    def __str__(self):
        return str(object.__getattribute__(self, '_property')())

    def __repr__(self):
        return repr(object.__getattribute__(self, '_property')())

'''Setup'''

local = threading.local()

application = Application(
    Config(),
    Router(()),
    )

config = PropertyProxy(application._get_config)
router = PropertyProxy(application._get_router)
request = PropertyProxy(application._get_request)
response = PropertyProxy(application._get_response)


'''Utility JSON methods'''

class ComplexJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '__iter__'):
            return list(obj)

        if hasattr(obj, 'isoformat'):
            return obj.isoformat()

        if isinstance(obj, object) and hasattr(obj, '__dict__'):
            return self._encode_std_object(obj)

        elif isinstance(obj, object) and hasattr(obj, '__slots__'):
            return self._encode_lite_object(obj)

        else:
            return

        return json.JSONEncoder.default(self, obj)

    def _encode_std_object(self, obj):
        newobj = {}
        
        '''
        # class attributes
        # causing problems with thrift class attrs (thrift_spec, instancemethods, etc)
        newobj.update(dict(
            (name, value)
            for name, value
            in dict(obj.__class__.__dict__).iteritems()
            if name[0] != '_'
            ))
        '''
        
        # object attributes
        newobj.update(dict(
            (name, value)
            for name, value
            in obj.__dict__.iteritems()
            if ord(name[0].lower()) in xrange(97,123)
            ))
        
        newobj['__name__'] = obj.__class__.__name__
        
        return newobj
    
    def _encode_lite_object(self, obj):
        newobj = {}

        for slot in obj.__slots__:
            if ord(slot[0].lower()) in xrange(97,123):
                try:
                    newobj[slot] = getattr(obj, slot)
                except AttributeError:
                    newobj[slot] = None
                    
        newobj['__name__'] = obj.__class__.__name__
        
        return newobj
    
'''Utility XML/XSL classes'''


class XMLEncoder(object):

    _is_uuid = re.compile(r'^\{?([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})\}?$', re.I)

    def __init__(self, data, doc_el='document', encoding='UTF-8', **params):
        if type(data) is dict and \
           len(data) == 2 and \
           '__error__' in data and \
           '__message__' in data:
            doc_el='error'

        self.data = data
        self.document = etree.Element(doc_el, **params)
        self.encoding = encoding

    
    def to_string(self, indent=True, declaration=True):
        xml = self.to_xml()
        if indent:
            self._indent(xml)
        output = etree.tostring(xml, encoding=self.encoding, xml_declaration=declaration)
        return output


    def to_xml(self):
        if self.data:
            self.document = self._update_document(self.document, self.data)
        return self.document


    def _update_document(self, node, data):

        if type(data) == bool and data:
            node.set('nodetype', u'boolean')
            node.text = u"true"

        elif type(data) == bool:
            node.set('nodetype', u'boolean')
            node.text = u"false"
        
        elif isinstance(data, basestring) and \
             len(data) in (36, 38) and \
             self._is_uuid.match(data):

            try:
                UUID(data)
            except:
                pass
            else:
                node.set('nodetype', u'uuid')
            finally:
                node.text = escape(self._to_unicode(data))

        elif hasattr(data, 'isoformat'):
            node.set('nodetype', u'timestamp')
            node.text = data.isoformat()

        elif data is None:
            node.text = None

        elif self._is_scalar(data):
            node.text = escape(self._to_unicode(data))

        elif type(data) == dict:
            for name, items in data.iteritems():
                if isinstance(name, basestring) and name != '' and str(name[0]) is '?':
                    ''' processing instruction '''
                    #self._add_processing_instruction(node, items)
                    pass

                elif isinstance(name, basestring) and name != '' and str(name[0]) is '!':
                    ''' doctype '''
                    #self._add_docype(node, items)
                    pass
                
                    
                elif isinstance(name, basestring) and name != '' and not name[0].isalpha():
                    child = etree.SubElement(node, u'node', name=unicode(name))
                    
                elif isinstance(name, basestring) and name != '':
                    child = etree.SubElement(node, unicode(name))

                else:
                    child = etree.SubElement(node, u"node", name=unicode(name))

                child = self._update_document(child, items)

        elif type(data) == list and any(self._is_scalar(i) for i in data):
            node.set('nodetype',u'list')
            for item in data:
                child = etree.SubElement(node, u'i')
                child = self._update_document(child, item)

        elif type(data) == list:
            node.set('nodetype',u'list')
            for item in data:
                child = self._update_document(node, item)

        elif type(data) == set:
            node.set('nodetype',u'unique-list')
            for item in data:
                child = etree.SubElement(node, u'i')
                child = self._update_document(child, item)

        elif type(data) == tuple:
            node.set('nodetype',u'fixed-list')
            for item in data:
                child = etree.SubElement(node, u'i')
                child = self._update_document(child, item)

        elif isinstance(data, object):
            children = []
            
            if hasattr(data, '__dict__'):
                children = [(n, v) for n, v in data.__dict__.iteritems() if n[0] is not '_' and not hasattr(n, '__call__')]
                
            if hasattr(data, '__slots__'):
                children = [(n, getattr(data, n)) for n in data.__slots__ if n[0] is not '_' and not hasattr(n, '__call__')]

            sub = etree.SubElement(node, unicode(data.__class__.__name__), nodetype="container")

            for item, value in children:
                child = etree.SubElement(sub, unicode(item))
                child = self._update_document(child, value)

        elif type(data) is file:
            pass

        else:
            raise Exception('self._update_document: unsupported type "%s"' % type(data))

        return node


    def _is_scalar(self, value):
        return isinstance(value, (basestring, float, int, long))
    

    def _indent(self, elem, level=0):
        i = "\n" + "  "*level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    def _to_unicode(self, string):
        if not string and not self._is_scalar(string):
            return u''
        return unicode(self.escape(string))


    def _add_processing_instruction(self, node, data):

        self.document = etree.ElementTree(self.document)
        
        attrs = []

        if type(data) is dict:
            attrs = self.__dict_to_attrs(dict( (name, value) for name, value in data.iteritems() if name[0].isalpha() and type(value) is not dict  ))

        #pi = etree.ProcessingInstruction(node[1:])#, ' '.join(attrs))
        pi = etree.ProcessingInstruction('xml-stylesheet', 'type="text/xml" href="default.xsl"')

    
    def __dict_to_attrs(self, d):
        return [str(name) + '="' + str(value) + '"' for name, value in d.iteritems()]


    def escape(self, data):
        if data is None:
            return None

        if isinstance(data, unicode):
            return data
            #return str(self.unicodeToHTMLEntities(data))
        elif isinstance(data, str):
            try:
                data = unicode(data, 'latin1')
            except:
                pass
            return data
            #return str(self.unicodeToHTMLEntities(data))
        else:
            return data
            #return str(self.unicodeToHTMLEntities(str(data)))


    def unicodeToHTMLEntities(self, text):
        """Converts unicode to HTML entities.  For example '&' becomes '&amp;'."""
        text = cgi.escape(text).encode('ascii', 'xmlcharrefreplace')
        #text = text.encode('ascii', 'xmlcharrefreplace')
        #text = cgi.escape(text).encode('UTF-8', 'xmlcharrefreplace')
        return text


class LocalFileResolver(etree.Resolver):
    def __init__(self, path):
        self.path = path
        
    def resolve(self, url, id, context):
        if url.startswith('local:'):
            return self.resolve_filename(self.path, url.replace('local:', ''))


class XSLTranslator(object):

    extensions = []
    path = ''
    xml = None
    xsl = None
    params = {}
    resolvers = []

    def __init__(self, xml=None, stylesheet=None, path=None, extensions=[], params={}, resolvers=[]):
        if path:
            self.path = path

        if extensions:
            self.extensions = extensions

        if params:
            self.params = params

        if resolvers:
            self.resolvers = resolvers

        self._load_xml(xml)
        self._find_processing_instructions()
        self._load_stylesheet(stylesheet)
        self._configure_extensions()

    def set_params(self, **params):
        self.params = params


    def _find_processing_instructions(self):
        """
        Not Implemented
        
        processing_instructions = self.xml.xpath('/processing-instruction("xml-stylesheet")[not(@alternate)]')
        if processing_instructions:
            href = str(processing_instructions[0].get('type'))
            if href[-4:] is '.xsl':
                stylesheet = href
        """
        pass

    def _configure_extensions(self):
        for extension in self.extensions:
            module = extension(**self.params)

            ns = etree.FunctionNamespace(module.ns[1])
            ns.prefix = module.ns[0]

            for key in [n for n in dir(module) if n[0] != '_' and hasattr(getattr(module, n), '__call__')]:
                ns[re.sub('_', '-', key)] = getattr(module, key)

     
        
    def _transform(self, xml=None, xsl=None):
        if xml is not None:
            self._load_xml(xml)
        
        if xsl is not None:
            self._load_stylesheet(xsl)

        if self.xml is None:
            raise FormatterError('no xml available for transformation')

        if self.xsl is None:
            raise FormatterError('no stylesheet available for transformation')
        
        transform = etree.XSLT(self.xsl)
        return transform.apply(self.xml)


    def to_xml(self, xml=None, xsl=None):
        return self._transform(xml, xsl)


    def to_string(self, xml=None, xsl=None):
        return etree.tostring(self.to_xml(xml, xsl)) or ''


    def _load_xml(self, xml):
        if type(xml) is str and os.path.isfile(xml):
            self.xml = file(xml).read()

        elif type(xml) is str:
            self.xml = etree.fromstring(xml)

        else:
            self.xml = xml

        self.xml = etree.ElementTree(self.xml)


    def _load_stylesheet(self, stylesheet):
        if stylesheet:
            parser = self._get_xsl_parser()

            if type(stylesheet) is str and os.path.isfile(stylesheet):
                xsl = file(stylesheet)

            elif type(stylesheet) is str and os.path.isfile(self.path + stylesheet):
                xsl = file(self.path + stylesheet)

            elif type(stylesheet) is str:
                xsl = StringIO(stylesheet)

            try:
                self.xsl = etree.parse(xsl, parser)
            except etree.XMLSyntaxError:
                raise Exception('Stylesheet is invalid')


    def _get_xsl_parser(self):
        parser = etree.XMLParser()

        for resolver in self.resolvers:
            parser.resolvers.add(resolver)

        return parser


    def _get_output_encoding(self):
        if not has_attr(self, '_encoding'):
            encoding = self.output_node.get('encoding')
            if encoding:
                self._encoding = encoding
            else:
                self._encoding = None

        return self._encoding



    def _get_media_type(self):
        if self.output_node.get('media-type'):
            return self.output_node.get('media-type')

        if self.root_node is 'html':
            return 'text/html'

        if self.root_node in ('atom','rss','rdf','xsl','svg','xhtml'):
            return 'application/'+ self.root_node + '+xml'

        if self.root_node in ('xml','fo'):
            return 'application/xml'

        return 'text/plain'


    def _find_output_node(self):
        if not hasattr(self, '_output_node'):
            node = self.xsl.xpath('//xsl:output[1]', namespaces={'xsl': "http://www.w3.org/1999/XSL/Transform"})
            if node:
                self._output_node = node[0]
            else:
                self._output_node = None

        return self._output_node


    def _find_root_node(self):
        if not hasattr(self, '_root_node'):
            node = self.xsl.xpath('//xsl:template[@match="/"][1]/*[1]', namespaces={'xsl': "http://www.w3.org/1999/XSL/Transform"})
            if node and node[0].get('xmlns') and 'xhtml' in node[0].get('xmlns'):
                self._root_node = 'xhtml'
            elif node:
                self._root_node = str(node[0].tag)
            else:
                self._root_node = None

        return self._root_node


    output_node = property(_find_output_node)
    root_node = property(_find_root_node)
    contenttype = property(_get_media_type)
    encoding = property(_get_output_encoding)



class XPathCallbacks(object):

    ns = ('fwrd', 'http://fwrd.org/fwrd.extensions')

    def __init__(self, **kwargs):
        self._params = kwargs

    def param(self, _, name, method=''):
        if method.upper() not in ('PATH','GET','POST','SESSION'):
            params = self._params['request'].params
        else:
            params = self._params['request'][method.upper()]

        if name in params:
            return params[name]

        return None

    def params(self, _, method=''):
        if method.upper() not in ('PATH','GET','POST','SESSION'):
            params = self._params['request'].params
        else:
            params = self._params['request'][method.upper()]

        return XMLEncoder(params, doc_el='params').to_xml()

    """
    def config(self, _):
        return list(XMLEncoder(dict((key, value) for key, value in fwrd.config.iteritems()), doc_el='config').to_xml())
    """
    
    def session(self, _):
        return XMLEncoder(dict(self._params['request'].session), doc_el='session').to_xml()

    def environ(self, _):
        return XMLEncoder(self._params['request'].environ, doc_el='environ').to_xml()

    def title(self, _, items):
        if isinstance(items, basestring):
            return items.title()

        resp = []

        for item in items:
            if isinstance(item, basestring):
                resp.append(item.title())
            else:
                newitem = copy.deepcopy(item)
                try:
                    newitem.text = newitem.text.title()
                except:
                    pass
                resp.append(newitem)

        return resp


    def lower(self, _, items):
        if isinstance(items, basestring):
            return items.lower()

        resp = []

        for item in items:
            if isinstance(item, basestring):
                resp.append(item.lower())
            else:
                newitem = copy.deepcopy(item)
                newitem.text = newitem.text.lower()
                resp.append(newitem)
                
        return resp


    def upper(self, _, items):
        if isinstance(items, basestring):
            return items.upper()
        
        resp = []

        for item in list(items):
            if isinstance(item, basestring):
                resp.append(item.upper())
            else:
                newitem = copy.deepcopy(item)
                newitem.text = newitem.text.upper()
                resp.append(newitem)

        return resp


    def strip(self, _, items):
        if isinstance(items, basestring):
            return items.strip()
        
        resp = []

        for item in list(items):
            if isinstance(item, basestring):
                resp.append(item.strip())
            else:
                newitem = copy.deepcopy(item)
                if newitem.text is not None:
                    newitem.text = newitem.text.strip()
                    resp.append(newitem)

        return resp


    def trim(self, _, items):
        return self.strip(_, items)


    def coalesce(self, _, *args, **kwargs):
        for item in args:
            if isinstance(item, basestring) and item.trim() != '':
                return item
            if hasattr(item, 'text') and item.text != '':
                return item
            if item:
                return item

    def join(self, _, sep, items):
        resp = []

        for item in items:
            if hasattr(item, 'text'):
                resp.append(item.text)
            elif isinstance(item, basestring):
                resp.append(item)
            else:
                resp.append(unicode(item))
        
        return sep.join(resp)
                

    def dateformat(self, _, elements, format):
        print elements
        try:
            returned = []
            for item in elements:
                newitem = copy.deepcopy(item)
                newitem.text = self.__unescape(unicode(iso8601.parse_date(newitem.text).strftime(format)))
                returned.append(newitem)
            return returned

        except:
            raise
            return elements

    def timeformat(self, _, elements, outformat, informat='%Y-%m-%dT%H:%M:%S'):
        try:
            returned = []
            for item in elements:
                newitem = copy.deepcopy(item)
                value = datetime.strptime(newitem.text, informat)
                newitem.text = self.__unescape(unicode(value.strftime(outformat)))
                returned.append(newitem)
            return returned

        except:
            raise
            return elements

    def isempty(self, _, items):

        if not items:
            return True

        if len(items) > 1:
            return False

        if len(items) <= 0:
            return True

        item = items[0]

        if hasattr(item, 'text') and item.text is None:
            return True
            
        if hasattr(item, 'text') and str(item.text).strip() == '':
            return True
            
        if isinstance(item, basestring) and str(item).strip() == '':
            return True

        return False


    def range(self, _, start, stop, step=None):
        if step:
            return u','.join([unicode(i) for i in xrange(int(start), int(stop), int(step))])
        
        return u','.join([unicode(i) for i in xrange(int(start), int(stop))])

    def range_as_nodes(self, _, start, stop, step=None):
        return etree.XML([u'<item>%d</item>' % i for i in xrange(int(start), int(stop))])


    def __unescape(self, s):
        want_unicode = False
        if isinstance(s, unicode):
            s = s.encode("utf-8")
            want_unicode = True
        
        # the rest of this assumes that `s` is UTF-8
        list = []
        
        # create and initialize a parser object
        p = xml.parsers.expat.ParserCreate("utf-8")
        p.buffer_text = True
        p.returns_unicode = want_unicode
        p.CharacterDataHandler = list.append
        
        # parse the data wrapped in a dummy element
        # (needed so the "document" is well-formed)
        p.Parse("<e>", 0)
        p.Parse(s, 0)
        p.Parse("</e>", 1)
        
        # join the extracted strings and return
        es = ""
        if want_unicode:
            es = u""
        return es.join(list)





"""
    FWRD
    ====

    FWRD is a Python microframework designed to keep
    things simple for the developer.

    :copyright: 2011 by Phillip B Oldham
    :licence: MIT, please see the licence file

"""

import cgi
import collections
import copy
import functools
import inspect
import os
import sys
import threading
import traceback
import urllib
import xml.parsers.expat
import yaml

from datetime import datetime
from lxml import etree
from resolver import resolve as resolve_import
from uuid import UUID
from wsgiref.headers import Headers as WSGIHeaderObject
from xml.sax.saxutils import unescape as xml_unescape

from __version__ import *

try:
    import re2 as re
except ImportError:
    import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from urlparse import parse_qs, parse_qsl
except ImportError:
    from cgi import parse_qs, parse_qsl

try:
    # simplejson is faster than the
    # standard json module, so use it
    # when available
    import simplejson as json
except ImportError:
    import json


try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


__all__ = (
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

    # Config exceptions
    'ConfigError',
    'RouteCompilationError',
    )

# Global variables

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


# Utility Exceptions for error codes

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
    """Raise this object to return a ``404 Not Found`` HTTP error response to the client."""
    
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
    """Raise this object to return a ``403 Forbidden`` HTTP error response to the client."""
    code = 403
    def __init__(self, message="Forbidden", *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        print >>config.output, message
        self.message = message



class HTTPRedirection(HTTPError):
    code = 300
    def __init__(self, location):
        self.headers = HeaderContainer()
        self.headers['location'] = location
        self.message = ''



class NotModified(HTTPRedirection):
    """Raise this object to return a ``304 Not Modified`` HTTP response to the client."""
    code = 304
    def __init__(self):
        """Not Modified doesn't issue a Location header"""
        self.headers = HeaderContainer()



class Found(HTTPRedirection):
    """Raise this object to return a ``302 Found`` HTTP response to the client."""
    code = 302
    def __init__(self):
        """Found doesn't issue a Location header"""
        self.headers = HeaderContainer()



class Redirect(HTTPRedirection):
    """Raise this object to return a ``307 Redirect`` HTTP redirect response to the client."""
    code = 307



class Moved(HTTPRedirection):
    """Raise this object to return a ``301 Moved`` HTTP redirect response to the client."""
    code = 301



class SeeOther(HTTPRedirection):
    """Raise this object to return a ``303 See Other`` HTTP redirect response to the client."""
    code = 303


class InternalRedirect(Exception):
    """Raise this object to call another 
    
    """
    def __init__(self, callable, args={}):
        if isinstance(callable, basestring):
            self.callable = resolve(callable)
        elif hasattr(callable, '__call__'):
            self.callable = callable
        else:
            raise Exception('`callable` is not a callable')
        self.args = args

# Main application objects

class ConfigError(Exception):
    pass



class Config(threading.local):
    __slots__ = (
        'debug',
        'host',
        'port',
        'output',
        'format',
        'default_format',
        '_app_path',
        )


    def __init__(self, **kwargs):
        self.debug = False
        self.host = ''
        self.port = 8000
        self.default_format = None
        self.output = sys.stdout
        self.format = {}

        self.update(**kwargs)


    def update(self, **kwargs):
        for key, value in kwargs.iteritems():
            if key.lower() in self.__slots__:
                setattr(self, key.lower(), value)

    def _set_app_path(self, val):
        self._app_path = val
        sys.path.insert(0, self._app_path)

    def _get_app_path(self):
        if hasattr(self, '_app_path') and self._app_path:
            return self._app_path
        else:
            return os.getcwd()

    app_path = property(_get_app_path, _set_app_path)


class Application(threading.local):
    __slots__ = (
        '_config',
        '_router',
        '_request',
        '_response',
        '_middleware',
        )


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


    def reset(self):
        """Reset the current config and routing map with blank objects"""
        self._config = Config()
        self._router = Router(())
        self._middleware = []


    def setup(self, config):
        """Parse a config file and apply the settings."""
        try:
            try:
                stream = config.read()
            except (AttributeError, TypeError):
                stream = file(config).read()
        except (AttributeError, TypeError):
            stream = config

        try:
            config = CaseInsensitiveDictMapper(yaml.load(stream))

        except yaml.YAMLError as e:
            error = 'Import failed with malformed config'
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                error += ' at: (%s:%s)' % (mark.line+1, mark.column+1)
            raise ConfigError(error)

        if not self._validate_imported_config(config):
            raise ConfigError('Import failed: config invalid')

        if 'config' in config:
            self._update_config_from_import(config['config'])

        if 'global filters' in config:
            self._update_global_filters_from_import(config['global filters'])

        if 'routes' in config:
            self._update_routes_from_import(config['routes'])


    def _validate_imported_config(self, config):
        return any([x in config for x in ['config', 'routes', 'formats']])


    def _update_config_from_import(self, config):
        self._config.update(**config)


    def _update_routes_from_import(self, routes):
        self._router.urls = routes


    def _update_global_filters_from_import(self, filters):
        self._router._global_filters = [dict(filter_) for filter_ in filters]

        for filter_ in filters:
            try:
                self._router._global_filters_imported.append({
                    'callable': resolve(filter_['callable']),
                    'args': filter_.get('args', None)
                    })
                
            except ImportError:
                raise RouteCompilationError('unable to import global filter "%s"' % filter_['callable'])
            

    def _execute_callable(self):

        item, path_params = self._router.find(self._request.method, self._request.path[0])
        self._request.set_path_params(path_params)
        self._request.route = item.route

        try:
            return item(**self._request.params)

        except TypeError as e:
            "Additional request params were found. Attempt to re-run the request without those params"
            accepted_params = set(item._expected_args) & set(self._request.params.keys())
            return item(**dict( (k,v) for k, v in self._request.params.iteritems() if k in accepted_params ))

            
    def process_request(self):

        headers = {}
        code = 200
        body = None

        try:
            body = {
                'content': self._execute_callable(),
                'errors': self._response.errors,
                }

        except (KeyboardInterrupt, SystemExit) as e:
            print >>self._config.output, "Terminating."

        except InternalRedirect as e:
            raise NotImplementedError()

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
        """Register a middleware component"""
        self._middleware.append((middleware, opts))


    def run(self, server_func=None, host=None, port=None, debug=False, **kwargs):
        """Start the WSGI server"""

        if server_func is None and debug:
            server_func = self._serve_once

        elif server_func is None and self._config.debug:
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



# Routing


class RouteCompilationError(Exception):
    pass



class Route(object):
    __slots__ = (
        '__none__',
        '_callable',
        '_compiled_regex',
        '_compiled_callable',
        '_route_params',
        '_all_args',
        '_expected_args',
        '_preset_args',
        '_accepts_kwargs',
        '_allowed_methods',
        '_request_filters',
        'route',
        'regex',
        'callable',
        'allowed_formats',
        'request_filters'
        )

    _http_methods = ('HEAD', 'GET', 'POST', 'PUT', 'DELETE')

    _tuple_pattern = ('route', 'callable', 'methods', 'filters', 'formats')

    _compile_patterns = (
        # optional route items
        (r'\[', r'('),
        (r'\]', r')?'),

        # named path parameters
        (r'(?<!\\):(\w+)', r'(?P<\1>[^/]+)'),

        #
        (r'(?<!\\)_', r'[\s_]'),
        (r'\\_', r'_'),
        (r'\s+', r'\s+'),
        (r'(%)', r'\w'),
        (r'(\*)', r'\w+'),
        (r'([$!])', r'\\\1'),

        # fix parameters which contain underscores
        (r'(\(\?P\<\w*)\[\\s_\](\w*\>)', r'\1_\2'), 
        )

    _route_tests = (
        (r'(\/\w+)?(\/?\[\/?:[\w]+\]){2,}','Consecutive conditional parameters are not allowed'),
        (r'\/\[\/', r'Syntax error: "/[/" not allowed'),
        (r'(?<![\[\/-\\]):', r'Constant/keyword mix not allowed without a valid separator: "/", or "-"'),
        (r'(\|.+)$', r'Partial route contains noise after break'),
        )

    _param_search = re.compile(r'(?<!\[)/(?<!\\):(\w+)')


    def __init__(self, route, callable, methods='GET', filters=[], formats=[], prefix=None):
        def __none__(*args, **kwargs): pass
        self.__none__ = __none__
        
        self.route = route
        self.request_filters = filters
        self._set_allowed_methods(methods)
        self._compile_callable(callable)
        self._compiled_regex, self.regex = self._compile_regex(route, prefix=prefix)
        self._route_params = self._param_search.findall(self.route)
        self._validate()


    def __call__(self, **kwargs):
        return self._compiled_callable(**kwargs)


    def _compile_callable(self, callable):
        if isinstance(callable, basestring) and callable.lower == 'none':
            self._callable = None
            self.callable = "None"

        elif callable is None:
            self._callable = None
            self.callable = "None"

        elif isinstance(callable, basestring):
            try:
                self.callable = callable
                self._callable = resolve(self.callable)
            except ImportError:
                raise RouteCompilationError(
                    'unable to import callable "%s", searching %s with sys.path [%s]' % (
                        self.callable,
                        config.app_path,
                        ", ".join(sys.path)
                        )
                    )

        elif hasattr(callable, '__call__'):
            self._callable = callable
            self.callable = callable.__name__

        else:
            raise RouteCompilationError('callable "%s" cannot be processed' % self.callable)

        self._import_filters()
        self._compile_filters()
        self._process_argspec()


    def _import_filters(self):
        self._request_filters = []

        for filter_ in self.request_filters:
            try:
                self._request_filters.append({
                    'callable': resolve(filter_['callable']),
                    'args': filter_.get('args', None)
                    })
            except TypeError:
                raise RouteCompilationError('incorrect syntax used for filter; should be a list')
            except ImportError:
                raise RouteCompilationError('unable to import callable for filter "%s"' % filter_['callable'])
                

    def _compile_filters(self):

        _callable = self._callable
        
        if not _callable:
            _callable = self.__none__

        filters = router._global_filters_imported + self._request_filters

        if not filters:
            self._compiled_callable = _callable
            return

        for filter_ in reversed(filters):
            if filter_['args'] is not None and isinstance(filter_['args'], (CaseInsensitiveDict, dict)):
                _callable = filter_['callable'](**dict(filter_['args']))(_callable)

            elif filter_['args'] is not None and isinstance(filter_['args'], (list, tuple, set)):
                _callable = filter_['callable'](*filter_['args'])(_callable)

            elif filter_['args'] is not None:
                _callable = filter_['callable'](filter_['args'])(_callable)

            else:
                _callable = filter_['callable'](_callable)

        self._compiled_callable = _callable


    def _process_argspec(self):
        self._accepts_kwargs = False
        self._all_args = []
        self._expected_args = []
        self._preset_args = []

        try:
            argspec = inspect.getargspec(self._callable)
        except TypeError:
            return

        self._accepts_kwargs = argspec.keywords != None

        # skip the "self" arg for class methods
        if inspect.ismethod(self._callable):
            self._all_args = argspec.args[1:]
        else:
            self._all_args = argspec.args

        try:
            self._expected_args = self._all_args[:-len(argspec.defaults)]
        except TypeError:
            self._expected_args = self._all_args

        try:
            self._preset_args = self._all_args[-len(argspec.defaults):]
        except TypeError:
            self._preset_args = self._all_args


    def _validate(self):
        self._validate_route_args_are_not_repeated()
        self._validate_route_args_match_callable()


    def _validate_route_args_are_not_repeated(self):
        if len(self._route_params) != len(set(self._route_params)):
            raise RouteCompilationError('Route params can not be repeated')


    def _validate_route_args_match_callable(self):
        if not self._callable or self._callable is self.__none__:
            return
        
        if self.route[0] is '^':
            return
        
        if self._route_params and \
            len(self._route_params) < len(self._expected_args) \
            and not self.accepts_kwargs:
            raise RouteCompilationError(
                'Route param list (%s) does not match callable args (%s) for route "%s" -> (%s)' %
                (', '.join(set(self._route_params)),
                 ', '.join(set(self._expected_args)),
                 self.route,
                 self.callable))

        difference = set(self._route_params) - set(self._expected_args) 
        if difference and not self.accepts_kwargs:
            raise RouteCompilationError(
                'Route param list (%s) does not match arg list for "%s" -> (%s)' %
                (', '.join(set(self._route_params)),
                 self.callable,
                 ', '.join(difference)))
        

    @classmethod
    def _compile_regex(cls, pattern, prefix=''):
        if str(pattern[0]) is '^':
            regex = r'^' + prefix + pattern[1:]

        else:
            regex = prefix + pattern

            for test, reason in cls._route_tests:
                if re.search(test, regex):
                    reason += "\n  while testing %s" % regex
                    raise RouteCompilationError(reason)

            for search, replace in cls._compile_patterns:
                regex = re.sub(search, replace, regex)
                
            if pattern[-1] is '|':
                regex = r'^' + regex[:-1]
            else:
                regex = r'^' + regex + r'$'

        try:
            return re.compile(regex), regex
            
        except Exception as e:
            raise RouteCompilationError(e.message+' while testing: %s' % regex)


    def _set_allowed_methods(self, methods):
        if isinstance(methods, basestring):
            self._allowed_methods = [method.upper() for method in re.split('\W+', methods) if method.upper() in self._http_methods]

        elif isinstance(methods, (tuple, list)):
            self._allowed_methods = [method.upper() for method in methods if method.upper() in self._http_methods]

        else:
            self._allowed_methods = ['GET']


    def _get_allowed_methods(self):
        return self._allowed_methods


    def _callable_expects_args(self):
        return self._expected_args != []


    def _callable_accepts_kwargs(self):
        return self._accepts_kwargs


    def test(self, test):
        try:
            return self._compiled_regex.search(test).groupdict()
        except:
            return None


    methods = property(_get_allowed_methods, _set_allowed_methods)
    expects_args = property(_callable_expects_args)
    accepts_kwargs = property(_callable_accepts_kwargs)



class Router(object):
    """An object which contains the application's URL routing map."""
    __slots__ = (
        '_global_filters',
        '_global_filters_imported',
        '_routes',
        'HEAD',
        'GET',
        'POST',
        'PUT',
        'DELETE',
        )


    def __init__(self, urls=None):
        self._global_filters = []
        self._global_filters_imported = []

        self.clear()
        
        if urls:
            self._set_urls(urls)


    def __call__(self, *args, **kwargs):
        return self.find(*args, **kwargs)


    def __getitem__(self, name):
        return getattr(self, name)


    def __setitem__(self, name, value):
        setattr(self, name, value)


    def _get_urls(self):
        return dict( (item, self[item]) for item in self.__slots__ if item[0] != '_' )


    def _set_urls(self, urls=None):
        self.clear()
        
        if urls and isinstance(urls, (list, tuple, dict, CaseInsensitiveDict)):
            self._define_routes(urls)

        else:
            raise RouteCompilationError('unable to define routes')


    def _define_routes(self, urls, prefix=''):
        # Basic structure: (route, callable [, http_method_list [, filter_list [, allowed_formats]]])
        # Prefix structure: (prefix, (tuple_of_basic_structure_tuples, ...))

        for item in urls:
            if not isinstance(item, (tuple, dict, CaseInsensitiveDict)):
                continue

            rule = dict((key, None) for key in Route._tuple_pattern)
            rule['prefix'] = prefix

            if isinstance(item, (list, tuple)):
                self.add(**dict(zip(Route._tuple_pattern, item)))

            elif isinstance(item, CaseInsensitiveDict):
                try:
                    self.add(**dict(item))
                except TypeError:
                    raise RouteCompilationError('specified route is empty')

            else:
                self.add(**item)


    def add(self, route, callable=None, methods='GET', prefix='', filters=[], formats=[]):
        """Add a route to the routing map"""
        
        item = Route(route, callable, methods, filters, formats, prefix)
        for method in item.methods:
            self[method][item.regex] = item


    def find(self, method, url):
        """Find a route based on the ``method`` and ``url``."""
        method = method.upper().strip()

        if len(url) > 1 and url[-1] == '/':
            url = url[:-1]

        for regex, item in self[method].iteritems():
            params = item.test(url)
            if params is not None:
                return item, params

        raise NotFound(url=url, method=method)


    def clear(self):
        """Clear the current routing map."""
        #self._global_filters = []
        #self._global_filters_imported = []
        for method in self.__slots__:
            if method[0] != '_':
                self[method] = OrderedDict()


    # Properties
    urls = property(_get_urls, _set_urls)



class HeaderContainer(threading.local):
    __slots__ = (
        'headers',
        )


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
    # Should a factory be used to create a request/response obj per "request"?
    __slots__ = (
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
        )

    _get_ext = re.compile(r'^(.+)\.([a-z]+)$')
    _is_float = re.compile(r'^\-?\d+\.\d+$')
    _is_named = re.compile(r'^(\w+)(\[.+\])$')

    _default_env = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '',
        'QUERY_STRING': '',
        }


    def __init__(self, environ=None, **kwargs):
        for slot in (slot for slot in self.__slots__ if slot.isupper()):
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
        self.GET = ParameterContainer().parse_qs(self.environ['QUERY_STRING'])


    def parse_body(self):
        if self.environ.get('CONTENT_TYPE', '').lower()[:10] == 'multipart/':
            fp = self.environ['wsgi.input']
            
        else:
            length = int(self.environ.get('CONTENT_LENGTH', 0) or 0)
            fp = StringIO(self.environ['wsgi.input'].read(length))

        self.POST = ParameterContainer().parse_qs(cgi.FieldStorage(fp=fp,
                                                                   environ=self.environ,
                                                                   keep_blank_values=True))


    def build_get_string(self):
        return self.build_qs(self.GET)

    
    def build_post_string(self):
        return self.build_qs(self.POST)

        
    def build_qs(self, params, key=None):
        """Return a HTTP querystring from the ``params`` passed."""
        parts = []
        
        if params and hasattr(params, 'items'):
            for name, value in params.items():
                
                if hasattr(value, 'values'):
                    # Encode a dict
                    parts.extend(self.build_qs(params=value.values(),
                                               key=self.build_qs_key(key, cgi.escape(name))))

                elif hasattr(value, '__iter__'):
                    # Encode an iterable (list, tuple, etc)
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
            return urllib.unquote(value)
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


    def _has_params(self):
        return self.get_params() != {}


    params = property(get_params, doc="A dict of parameters parsed from the request")
    session = property(get_session, doc="An interface to the ``session`` object (Beaker) if available")
    querystring = property(build_get_string, doc="The current request's GET querystring")
    poststring = property(build_post_string, doc="The current request's POST querystring")
    has_params = property(_has_params, doc="``True`` if the current request has parameters, ``False`` otherwise")



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
        return [output]


    def _set_code(self, code):
        self._code = code


    def _get_code(self):
        if not self._code:
            self._code = 200

        if not self._code in HTTP_STATUS_CODES:
            self._code = 500

        return "%d %s" % (self._code, HTTP_STATUS_CODES[self._code])


    def set_error(self, name, value):
        """Set an error message to be applied to the formatted response."""
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


# Default response formatters


class TranslatedResponse(Response):
    """Takes the response data and formats it first
    into XML then passes it through an XSL translator"""

    responsetype = 'xsl'
    extensions = (None, '', 'htm', 'html')
    contenttype = ''


    def __init__(self, start_response, request, config={}, **kwargs):
        super(self.__class__, self).__init__(start_response, request, config=config)
        self.params['stylesheet'] = None
        self.params['cache'] = True
        self._update_params(**kwargs)


    def format(self, data=None, **kwargs):

        if self.params['cache']:
            self._xsl = None

        xml = XMLEncoder(
            data,
            doc_el='response',
            encoding='UTF-8',
            request=self.request.path[0],
            route=self.request.route,
            method=self.request.method.lower()
            ).to_string()

        self.headers.replace('Content-Type', self.xsl.contenttype)

        return self.xsl.to_string(xml=xml)


    @property
    def xsl(self):
        if hasattr(self, '_xsl') and self._xsl:
            return self._xsl

        self.params['stylesheet'] = os.path.abspath(self.params['stylesheet'])

        if 'stylesheet' not in self.params or \
            not self.params['stylesheet']:
            raise ResponseParameterError("the stylesheet filename must be set")

        self.params['stylesheet_path'] = os.path.basename(self.params['stylesheet'])

        if not os.path.isfile(os.path.join(
            self.params['stylesheet_path'],
            self.params['stylesheet']
            )):
            raise ResponseParameterError('the stylesheet could not be found')

        xslfile = os.path.join(
            self.params['stylesheet_path'],
            self.params['stylesheet']
            )

        self._xsl = XSLTranslator(None,
                            xslfile,
                            path=self.params['stylesheet_path'],
                            extensions=[XPathFunctions],
                            params={
                                'request': self.request,
                                },
                            resolvers=[LocalFileResolver(self.params['stylesheet_path'])]
                            )        

        return self._xsl

class TextResponse(Response):
    """Takes the response data and formats it into
    a text representation"""

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
    """Takes the response data and converts it into
    a "generic" XML representation"""

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
    """Takes the response data and converts it into
    a "generic" JSON representation"""

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
    __slots__ = (
        '_property',
        )

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



# Setup

local = threading.local()

local.application = Application(
    Config(),
    Router(()),
    )

application = local.application
config = PropertyProxy(application._get_config)
router = PropertyProxy(application._get_router)
request = PropertyProxy(application._get_request)
response = PropertyProxy(application._get_response)



# Utility JSON methods

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
        
        # class attributes
        # causing problems with thrift class attrs (thrift_spec, instancemethods, etc)
        #newobj.update(dict(
        #    (name, value)
        #    for name, value
        #    in dict(obj.__class__.__dict__).iteritems()
        #    if name[0] != '_'
        #    ))
        
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


    
# Utility XML/XSL classes

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


    def from_string(self, string):
        self.data = etree.parse(StringIO(string))
            

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
                node.text = self._to_unicode(data)

        elif hasattr(data, 'isoformat'):
            try:
                node.text = data.isoformat()
                node.set('nodetype', u'timestamp')
            except TypeError:
                pass

        elif data is None:
            node.text = None

        elif self._is_scalar(data):
            node.text = self._to_unicode(data)

        elif hasattr(data, 'iteritems'):
            #node.set('nodetype',u'map')
            for name, items in data.iteritems():
                if isinstance(name, basestring) and name != '' and str(name[0]) is '?':
                    #  processing instruction 
                    #self._add_processing_instruction(node, items)
                    pass

                elif isinstance(name, basestring) and name != '' and str(name[0]) is '!':
                    # doctype 
                    #self._add_docype(node, items)
                    pass
                
                    
                elif isinstance(name, basestring) and name != '' and not name[0].isalpha():
                    child = etree.SubElement(node, u'node', name=unicode(name))
                    
                elif isinstance(name, basestring) and name != '':
                    child = etree.SubElement(node, unicode(name))

                else:
                    child = etree.SubElement(node, u"node", name=unicode(name))

                child = self._update_document(child, items)
        
        elif type(data) == list:
            node.set('nodetype',u'list')
            for item in data:
                child = etree.SubElement(node, u'i')
                child = self._update_document(child, item)

        elif hasattr(data, 'send'):
            # generator
            node.set('nodetype',u'generated-list')
            for item in data:
                child = etree.SubElement(node, u'i')
                child = self._update_document(child, item)

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
                children = ((n, v) for n, v in data.__dict__.iteritems() if n[0] is not '_' and not hasattr(n, '__call__'))
                
            if hasattr(data, '__slots__'):
                children = ((n, getattr(data, n)) for n in data.__slots__ if n[0] is not '_' and not hasattr(n, '__call__'))

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
            attrs = self.__dict_to_attrs(
                dict( (name, value)
                      for name, value
                      in data.iteritems()
                      if name[0].isalpha()
                      and type(value) is not dict
                      )
                )

        #pi = etree.ProcessingInstruction(node[1:])#, ' '.join(attrs))
        pi = etree.ProcessingInstruction(
            'xml-stylesheet',
            'type="text/xml" href="default.xsl"'
            )

    
    def __dict_to_attrs(self, d):
        return (str(name) + '="' + str(value) + '"' for name, value in d.iteritems())


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

            for key in (n for n in dir(module) if n[0] != '_' and hasattr(getattr(module, n), '__call__')):
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



class XPathFunctions(object):
    """
    .. highlight:: xslt

    ``FWRD`` provides a number of utility functions to the XSL formatter. To use these
    functions you need to add the ``fwrd:`` namespace as an extension namespace in your
    stylesheet::

        <xsl:stylesheet version="1.0"
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
            xmlns:fwrd="http://fwrd.org/fwrd.extensions"
            extension-element-prefixes="fwrd">
    
            ...
    
        </xsl:stylesheet>

    """

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


    #def config(self, _):
    #    return list(XMLEncoder(dict((key, value) for key, value in fwrd.config.iteritems()), doc_el='config').to_xml())

    
    def session(self, _):
        return XMLEncoder(dict(self._params['request'].session), doc_el='session').to_xml()


    def environ(self, _):
        return XMLEncoder(self._params['request'].environ, doc_el='environ').to_xml()


    def abs(self, _, items):
        """``fwrd:abs(string|node|nodeset)``

        Return the absolute value of elements provided.

        ::

            <xsl:value-of select"fwrd:abs('-1')" />
            <!-- output: 1 -->
        
        """

        if isinstance(items, basestring):
            return abs(items)

        resp = []

        for item in items:
            if isinstance(item, basestring):
                resp.append(abs(item))
            else:
                newitem = copy.deepcopy(item)
                try:
                    newitem.text = abs(newitem.text)
                except:
                    pass
                resp.append(newitem)

        return resp


    def ceil(self, _, items):
        """``fwrd:ceil(string|node|nodeset)``

        Return the ceiling of elements provided.

        ::

            <xsl:value-of select"fwrd:ceil('2.65')" />
            <!-- output: 3 -->
        
        """

        if isinstance(items, basestring):
            return ceil(items)

        resp = []

        for item in items:
            if isinstance(item, basestring):
                resp.append(ceil(item))
            else:
                newitem = copy.deepcopy(item)
                try:
                    newitem.text = ceil(newitem.text)
                except:
                    pass
                resp.append(newitem)

        return resp


    def floor(self, _, items):
        """``fwrd:floor(string|node|nodeset)``

        Return the floor of elements provided.

        ::

            <xsl:value-of select"fwrd:floor('2.65')" />
            <!-- output: 2 -->
        
        """

        if isinstance(items, basestring):
            return ceil(items)

        resp = []

        for item in items:
            if isinstance(item, basestring):
                resp.append(ceil(item))
            else:
                newitem = copy.deepcopy(item)
                try:
                    newitem.text = ceil(newitem.text)
                except:
                    pass
                resp.append(newitem)

        return resp


    def title(self, _, items):
        """``fwrd:title(string|node|noteset)``

        Return a titlecased version of the element; words start with uppercase
        characters, all remaining cased characters are lowercase.

        ::

            <xsl:value-of select="fwrd:title('some text')" />
            <!-- output: Some Text -->
        """
        
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
        """``fwrd:lower(string|node|noteset)``

        Return a copy of the element converted to lowercase.

        ::

            <xsl:value-of select="fwrd:lower('SOME TEXT')" />
            <!-- output: some text -->
        """
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
        """``fwrd:upper()``

        Return a copy of the element converted to uppercase.

        ::

            <xsl:value-of select="fwrd:upper('some text')" />
            <!-- output: SOME TEXT -->
        """
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
        """``fwrd:strip(string|node|noteset)``

        Return a copy of the element with leading and trailing white-space characters removed.

        ::

            <xsl:value-of select="fwrd:strip('    some text    ')" />
            <!-- output: some text -->
        """
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
        """``fwrd:trim()``

        Alias of fwrd:strip()"""
        return self.strip(_, items)


    def coalesce(self, _, *args, **kwargs):
        """``fwrd:coalesce(item, [item, ...])``

        Returns the first non-empty element.

        ::

            <xsl:value-of select="fwrd:coalesce('','','','some text')" />
            <!-- output: some text -->
        """
        for item in args:
            if isinstance(item, basestring) and item.strip() != '':
                return item
            if hasattr(item, 'text') and item.text.strip() != '':
                return item
            if item:
                return item


    def join(self, _, sep, items):
        """``fwrd:join(separator, seq<string|node|noteset>)``

        Return a string which is the concatenation of the elements in the sequence ``seq``
        separated by the string ``separator``.

        ::

            <xsl:value-of select="fwrd:coalesce('','','','some text')" />
            <!-- output: some text -->
        """
        resp = []

        for item in items:
            if hasattr(item, 'text'):
                resp.append(item.text)
            elif isinstance(item, basestring):
                resp.append(item)
            else:
                resp.append(unicode(item))
        
        return sep.join(resp)


    def utcnow(self, _, *args, **kwargs):
        """``fwrd:utcnow()``

        Return the current UTC date and time in the ISO 8601 combined date and
        time format (``YYYYMMDDThhmmssZ``).

        ::

            <xsl:value-of select="fwrd:utcnow()" />
            <!-- output: 2012-12-21T00:00:00Z -->
        """
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                

    def dateformat(self, _, elements, format):
        """``fwrd:dateformat(string|node|nodeset, output-format)``

        Accepts an ISO 8601 date formatted element and returns a string
        formatted according to the pattern ``output-format``, following
        the same rules as the _Python Datetime module::

            <xsl:value-of select="fwrd:dateformat('2012-12-21T00:00:00Z', '%A %B %d, %Y')" />
            <!-- output: Friday December 21, 2012 -->

        .. _Python Datetime module: http://docs.python.org/library/datetime.html#strftime-strptime-behavior

        """
        try:
            if isinstance(elements, basestring) and elements.strip() != '':
                return self._unescape(unicode(datetime.strptime(elements.strip()[:10], '%Y-%m-%d').strftime(format)))
            
            returned = []
            for item in elements:
                newitem = copy.deepcopy(item)
                newitem.text = self._unescape(unicode(datetime.strptime(newitem.text.strip()[:10], '%Y-%m-%d').strftime(format)))
                returned.append(newitem)
            return returned

        except:
            raise
        return elements


    def format_date(self, _, elements, format):
        """``fwrd:format-date(string|node|nodeset, output-format)``

        Alias of the ``fwrd:dateformat()`` function.
        """        
        return self.dateformat(_, elements, format)


    def timeformat(self, _, elements, outformat, informat='%Y-%m-%dT%H:%M:%S'):
        """``fwrd:timeformat(string|node|nodeset, output-format, input-format)``

        Accepts a string which is parsed according to pattern ``input-format`` and
        returns a string formatted according to the pattern ``output-format``.

        By default the pattern `input-format` is `%Y-%m-%dT%H:%M:%S`.
        
        Both `input-format` and `output-format` follow the same rules as the
        _Python Datetime module::

            <xsl:value-of select="fwrd:timeformat('2012-12-21T00:00:00Z',
                                                  '%Y-%m-%dT%H:%M:%SZ',
                                                  '%A %B %d %H:%M:%S %p %Y')" />
            <!-- output: Friday December 21 00:00:00 AM 2012 -->

        .. _Python Datetime module: http://docs.python.org/library/datetime.html#strftime-strptime-behavior

        """
        try:
            if isinstance(elements, basestring) and elements.strip() != '':
                value = datetime.strptime(elements, informat)
                return self._unescape(unicode(value.strftime(outformat)))
            
            returned = []
            for item in elements:
                newitem = copy.deepcopy(item)
                value = datetime.strptime(newitem.text, informat)
                newitem.text = self._unescape(unicode(value.strftime(outformat)))
                returned.append(newitem)
            return returned

        except:
            raise
        return elements


    def format_time(self, _, elements, outformat, informat='%Y-%m-%dT%H:%M:%S'):
        """fwrd:format-time(string|node|nodeset, output-format, input-format)

        Alias of the `fwrd:timeformat()` function.
        """
        return self.timeformat(_, elements, outformat, informat)


    def isempty(self, _, items):
        """``fwrd:isempty(string|node|nodeset)``

        Returns ``true()`` if the element is an empty string, node, or nodeset, ``false()`` otherwise.

        ::
        
            <xsl:value-of select="fwrd:isempty('')" />
            <!-- output: true() -->

        """
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


    def empty(self, _, items):
        """``fwrd:empty(string|node|nodeset)``
        
        Alias of the `isempty()` function.
        """
        return self.isempty(_, items)


    def _range(self, start, stop, step=1):
        r = start
        while r < stop:
            yield r
            r += step


    def range(self, _, start, stop, step=1):
        """``fwrd:range(start, stop[, step])``

        Returns a string of comma-separate integers starting from the integer ``start``,
        ending on or before the integer ``stop`` incrementing by the integer ``step`` which
        by default is 1.

        This method operates in the same manner as Python's ``range()`` method with the exception
        that a ``start`` argument is required::
        
            <xsl:value-of select="fwrd:range(1,10,2)" />
            <!-- output: 1,3,5,9 -->

        .. _Python's ``range()`` method: http://docs.python.org/library/functions.html#range

        """

        if not isinstance(start, (int, float)) or \
           not isinstance(stop, (int, float)) or \
           not isinstance(step, (int, float)):
            return False

        type_ = type(step)

        try:
            return u','.join((unicode(type_(i)) for i in self._range(start, stop, step)))
        except:
            return u','.join((unicode(type_(i)) for i in self._range(start, stop)))


    def range_as_nodes(self, _, start, stop, step=1):
        """``fwrd:range-as-nodes(start, stop[, step])``

        Returns a nodeset of integers starting from the integer ``start``,
        ending on or before the integer ``stop`` incrementing by the integer ``step`` which
        by default is 1.

        This method operates in the same manner as Python's ``range()`` method with the exception
        that a `start` argument is required::
        
            <xsl:value-of select="fwrd:range-as-nodes(1,10,2)" />
            <!-- output -->
            <items><item>0</item><item>1</item><item>3</item><item>5</item><item>9</item></items>

        .. _Python's ``range()`` method: http://docs.python.org/library/functions.html#range
        """

        if not isinstance(start, (int, float)) or \
           not isinstance(stop, (int, float)) or \
           not isinstance(step, (int, float)):
            return False

        type_ = type(step)

        try:
            return etree.XML(
                '<items>' +
                ''.join('<item>%s</item>' %
                        unicode(type_(i)) for i in
                        self._range(start, stop, step)) +
                '</items>')
        
        except:
            return etree.XML(
                '<items>' +
                ''.join('<item>%s</item>' %
                        unicode(type_(i)) for i in
                        self._range(start, stop)) +
                '</items>')


    def str_replace(self, _, elements, search_, replace_):
        """``fwrd:str-replace(string|node|nodeset, search, replace)``

        Returns a copy of the element with all occurrences of substring ``search`` replaced by ``replace``.

        ::

            <xsl:value-of select="fwrd:str-replace('foobar', 'ar', 'oz')" />
            <!-- output: fooboz -->

        """
        try:
            if isinstance(elements, basestring) and elements.strip() != '':
                return elements.replace(search_, replace_)
            
            returned = []
            for item in elements:
                newitem = copy.deepcopy(item)
                newitem.text = newitem.text.replace(search_, replace_)
                returned.append(newitem)
            return returned

        except:
            raise
        return elements


    def unescape(self, _, elements):
        """``fwrd:unescape(string|node|nodeset)``

        Returns a copy of the element with any escaped XML entities unescaped.

        ::
        
            <xsl:value-of select="fwrd:unescape('&amp; &amp;amp;')" />
            <!-- output: & &amp; -->

        """
        returned = []

        if isinstance(elements, basestring) and elements.strip() != '':
            return xml_unescape(elements)
        
        for item in elements:
            try:
                newitem = copy.deepcopy(item)
                newitem.text = xml_unescape(newitem.text)
                returned.append(newitem)
            except:
                returned.append(item)
        return returned


    def string_to_fragment(self, _, string):
        """``fwrd:string-to-fragment(string)``

        Provides a mechanism to convert a well-formed XML string to a
        "real" XML nodeset, which can then be queried/traversed as standard
        XML.

        Example::

            <xsl:value-of
                select="fwrd:string-to-fragment('<foo><bar /><spam>eggs</spam></foo>')/foo/spam"
                />
            <!-- output: eggs -->
        """
        pass

    def call_method(self, _, name, qs=None):
        """``fwrd:call-method(name, querystring)``

        Provides a mechanism to call the method ``name`` from within the webapp,
        optionally passing keyword arguments through ``querystring``. An XML
        nodeset returned.

        The method ``name`` should be of the same format used for ``callables`` in the
        config file.

        Arguments should be encoded in HTTP querystring format and passed as the
        ``querystring`` argument.

        For example::

            <xsl:variable
                name="items"
                select="fwrd:call-method('packagename.modulename:ClassName().method_name()',
                                         'spam=eggs&foo=bar'" />

        """
        if qs:
            params = ParameterContainer().parse_qs(qs)
        else:
            params = {}

        try:
            func = resolve(name)

            return XMLEncoder(
                func(**params),
                doc_el='result').to_xml()

        except ImportError as e:
            return self._encode_exception(e, name='ImportError')

        except AttributeError as e:
            return self._encode_exception(e, name='AttributeError')

        except TypeError as e:
            if 'takes no arguments' in str(e):
                return self._encode_exception(e, name='MethodTakesNoArgsError')

        except Exception as e:
            return self._encode_exception(e)


    def _encode_exception(self, e, name="Exception"):
        return XMLEncoder({'message': str(e),
                           'traceback': traceback.format_exc() },
                          doc_el=name).to_xml()
          

    def _unescape(self, s):
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



# General Utility Objects

class CaseInsensitiveDict(collections.Mapping):
    def __init__(self, d):
        self._d = d
        self._s = dict((k.lower(), k) for k in d)


    def __contains__(self, k):
        return k.lower() in self._s


    def __len__(self):
        return len(self._s)


    def __iter__(self):
        return iter(self._s)


    def __getitem__(self, k):
        return self._d[self._s[k.lower()]]


    def original_key(self, k):
        return self._s.get(k.lower())



def CaseInsensitiveDictMapper(d):
    if type(d) is dict:
        _d = {}
        for k, v in d.iteritems():
            _d[k] = CaseInsensitiveDictMapper(v)
        return CaseInsensitiveDict(_d)

    elif type(d) is list:
        return [CaseInsensitiveDictMapper(x) for x in d]

    elif type(d) is tuple:
        return tuple([CaseInsensitiveDictMapper(x) for x in d])

    elif type(d) is set:
        return set([CaseInsensitiveDictMapper(x) for x in d])

    else:
        return d



def resolve(callable):
    func = resolve_import(callable)

    if not func:
        raise ImportError()

    return func



class ParameterContainer(collections.Mapping):
    """Parameter Container Object

    This object parses parameters into a dict; automatically
    nesting, grouping, and updating values. The type of each
    value is inferred and set (integers, floats, booleans)
    where possible.

    Nested values/dicts can be created using the following
    querystring format:

    `?spam[level1][level2][level3]=eggs`

    which will stored as:

    >>> {'spam': {'level1': {'level2': {'level3': 'eggs'}}}}

    Values with the same key will be grouped in a list:

    `?a=1&a=2&a=3&a[]=4&a[]=5`

    would be stored as:

    >>> {'a': [1,2,3,4,5]}

    PLEASE NOTE:
    In a querystring which contains both simple and nested
    values, values later in the string, or to the right, will
    overwrite those earlier, or to the left:

    `?a=1&a=2&a[spam]=eggs`

    would be stored as:

    >>> {'a': {'spam': 'eggs'}}

    """

    _is_float = re.compile(r'^\-?\d+\.\d+$')
    _split_names = re.compile(r'\[([-\.\w]+)?\]')
    
    def __init__(self, params=None):
        self._params = params or {}


    def __contains__(self, k):
        return k in self._params


    def __len__(self):
        return len(self._params)


    def __iter__(self):
        return iter(self._params)


    def __getitem__(self, k):
        return self._params[k]


    def __eq__(self, other):
        return self._params.__eq__(other)


    def __repr__(self):
        return self._params.__repr__()


    def __str__(self):
        return self._params.__str__()


    def parse_qs(self, qs):
        if isinstance(qs, basestring):
            qs = self._parse_string(qs)
        elif isinstance(qs, cgi.FieldStorage):
            qs = self._parse_fieldstorage(qs)

        for key, value in qs:
            self._nest_params(self._clean_key(key),
                              value,
                              self._params)

        self._params = self._clean_values(self._params)

        return self


    def to_qs(self):
        """TODO"""
        pass


    def _parse_string(self, qs):
        return parse_qsl(self._clean_qs(qs), True)


    def _parse_fieldstorage(self, params):
        return self._parse_string("&".join('%s=%s' % (item.name, urllib.quote_plus(item.value)) for item in params.list))
        

    def _nest_params(self, keys, value, level):
        key = keys.pop(0) or '_'

        if key not in level:
            level[key] = {}

        if keys:
            if not isinstance(level[key], dict):
                level[key] = {}
            # recursivly add the next level
            self._nest_params(keys, value, level[key])
            
        else:
            if not isinstance(level[key], (dict, list)):
                # wrap scalar values in a list
                level[key] = [level[key]]

            if isinstance(level[key], list):
                # append scalar values to the list
                level[key].append(value)
                
            else:
                # store the scalar value
                level[key] = value


    def _clean_qs(self, qs):
        cleaned = []
        parsed = [tuple(item.split('=')) for item in qs.split('&')]

        for i in range(len(parsed)):
            try:

                k, v = parsed.pop(0)
                if k[-2:] == '[]':
                    k = k[:-2]
                cleaned.append((k, v))
            except ValueError:
                print parsed
                raise
            

        return "&".join("%s=%s" % (k, v) for k, v in cleaned)
                

    def _clean_key(self, key):
        return [i for i in self._split_names.split(key) if i is not '']


    def _clean_values(self, params):
        for key, value in params.iteritems():
            if isinstance(value, dict):
                params[key] = self._clean_values(value)

            elif isinstance(value, list):
                if len(value) > 1:
                    params[key] = self._update_type(value)
                elif len(value) == 1:
                    params[key] = self._update_type(value[0])

            else:
                params[key] = self._update_type(value)

        return params


    def _update_type(self, param):
        if isinstance(param, cgi.MiniFieldStorage):
            return param.value
        
        if type(param) is list and len(param) == 1:
            return self._update_type(param[0])
        
        if type(param) is list:
            return list(self._update_type(item) for item in param)
        
        if param.strip() == '':
            return None
        
        if self._is_float.match(param):
            return float(param)
        
        if len(param) > 1 and \
            param[0] is not '0' and \
            param.isdigit():
            return int(param)

        if len(param) == 1 and \
            param.isdigit():
            return int(param)
        
        if param.lower() == 'true':
            return True
        
        if param.lower() == 'false':
            return False
        
        return param

import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import Route, RouteCompilationError


class RouterSpec(unittest.TestCase):

    def setUp(self):
        self.router = Route()

    def it_should_compile_simple_routes(self):
        should_equal = (
            ('/', r'^/$'),
            ('/index', r'^/index$'),
            ('/foo/bar/baz', r'^/foo/bar/baz$'),
            ('/foo.bar/baz', r'^/foo.bar/baz$'),
            ('/foo.bar/baz.boz', r'^/foo.bar/baz.boz$'),
            ('/foo bar/baz boz', r'^/foo\s+bar/baz\s+boz$'),
            ('/foo_bar', r'^/foo[\s_]bar$'),
            ('/foo\_bar', r'^/foo_bar$'),
            ('/foo%/bar', r'^/foo\w/bar$'),
            ('/foo*/bar', r'^/foo\w+/bar$'),
            ('/foo!/$bar', r'^/foo\!/\$bar$'),
            )

        self._patterns_should_equal(should_equal)

    def it_should_compile_simple_parameters(self):
        should_equal = (
            ('/:foo', r'^/(?P<foo>[^/]+)$'),
            ('/:foo/:bar/:baz', r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)/(?P<baz>[^/]+)$'),
            )

        self._patterns_should_equal(should_equal)

    def it_should_compile_conditional_parameters(self):
        should_equal = (
            ('/[:foo]', r'^/((?P<foo>[^/]+))?$'),
            ('/:foo/:bar[/:baz]', r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)(/(?P<baz>[^/]+))?$'),
            )

        should_raise = (
            '/[:foo]/[:bar]',
            )

        self._patterns_should_equal(should_equal)
        self._patterns_should_raise(should_raise, exception=RouteCompilationError)

    def it_should_compile_partial_routes(self):
        should_equal = (
            ('/foo|', r'^/foo'),
            )

        should_raise = (
            '/foo|bar',
            )

        self._patterns_should_equal(should_equal)
        self._patterns_should_raise(should_raise, exception=RouteCompilationError)

    def it_should_compile_complex_regexes(self):
        should_equal = (
            (r'^/foo/bar$', r'^/foo/bar$'),
            (r'^/(index)?', r'^/(index)?'),
            (r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)(/(?P<baz>[^/]+))?$', r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)(/(?P<baz>[^/]+))?$'),
            )

        self._patterns_should_equal(should_equal)

    def it_should_add_simple_routes(self):
        def foo(): pass

        self.router.add('/', None)
        self.router.add('/foo', foo)
        self.router.add('/:foo', foo)
        self.router.add('/:foo/:bar', foo)
        self.router.add('/:foo[/:bar]', foo)
        self.router.add('/', foo, methods='POST')

        self.assertNotEqual(self.router.urls['GET'], [])
        self.assertNotEqual(self.router.urls['POST'], [])

        self.assertTrue('/:foo' in [route for route, regex, pattern, func in self.router.urls['GET']])
        self.assertTrue('/' in [route for route, regex, pattern, func in self.router.urls['GET']])
        self.assertTrue('/' in [route for route, regex, pattern, func in self.router.urls['POST']])

    def it_should_add_complex_routes(self):
        def foo(): pass

        self.router.add(r'^/$', None)
        self.router.add(r'^/index$', foo)
        self.router.add(r'^/(index)?', foo, methods='GET, POST')
        self.router.add(r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)(/(?P<baz>[^/]+))?$', foo)

        self.assertNotEqual(self.router.urls['GET'], [])
        self.assertNotEqual(self.router.urls['POST'], [])

        self.assertTrue(r'^/index$' in [route for route, regex, pattern, func in self.router.urls['GET']])
        self.assertTrue(r'^/(index)?' in [route for route, regex, pattern, func in self.router.urls['GET']])
        self.assertTrue(r'^/(index)?' in [route for route, regex, pattern, func in self.router.urls['POST']])

    def it_should_find_simple_routes(self):

        routes = (
            ('/', '/', 'GET', None),
            ('/index', '/index', 'POST', None),
            )

        for route, test, method, func in routes:
            self.router.add(route, func, methods=method)

            _func, _params, _route = self.router.find(method, test)

            self.assertEqual(route, _route)
            self.assertEqual(func, _func)
        
    def it_should_find_simple_parameters(self):
        routes = (
            ('/:foo', '/meh', {'foo': 'meh'}, 'GET', None),
            ('/foo/:bar', '/foo/meh', {'bar': 'meh'}, 'GET', None),
            ('/:foo/:bar', '/bur/meh', {'foo': 'bur', 'bar': 'meh'}, 'GET', None),
            )

        self._test_routes(routes)

    def it_should_find_simple_routes_with_special_chars(self):
        routes = (
            (r'/foo/\:bar', '/foo/:bar', {}, 'GET', None),
            (r'/foo/$bar', '/foo/$bar', {}, 'GET', None),
            (r'/foo/~bar', '/foo/~bar', {}, 'GET', None),
            (r'/foo/@bar', '/foo/@bar', {}, 'GET', None),
            (r'/foo_bar-baz', '/foo_bar-baz', {}, 'GET', None),
            (r'/foo|', '/foobarbaz', {}, 'GET', None),
            )

        self._test_routes(routes)

    def _test_routes(self, routes):
        for route, test, params, method, func in routes:
            self.router.add(route, func, methods=method)

            #print self.router.urls['GET']

            _func, _params, _route = self.router.find(method, test)

            self.assertEqual(route, _route)
            self.assertEqual(func, _func)
            self.assertEqual(params, _params)
            
    def _patterns_should_equal(self, patterns):
        for route, result in patterns:
            pattern, regex = self.router._compile(route)
            self.assertEqual(type(pattern), re._pattern_type)
            self.assertEqual(regex, result)
            
    def _patterns_should_raise(self, patterns, exception=Exception):
        for route in patterns:
            self.assertRaises(exception,
                              self.router._compile,
                              route)

import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import config, Route, Router, RouteCompilationError, NotFound


class RouterSpec(unittest.TestCase):

    def setUp(self):
        config.debug = True
        self.router = Router()
        self.router.clear()

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
            ('/:foo/:bar/:baz_boz', r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)/(?P<baz_boz>[^/]+)$'),
            )

        self._patterns_should_equal(should_equal)

    def it_should_compile_conditional_parameters(self):
        should_equal = (
            ('/[index]', r'^/(index)?$'),
            ('/[:foo]', r'^/((?P<foo>[^/]+))?$'),
            ('/:foo/:bar[/:baz]', r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)(/(?P<baz>[^/]+))?$'),
            ('/:foo/:bar_ber[/:_baz]', r'^/(?P<foo>[^/]+)/(?P<bar_ber>[^/]+)(/(?P<_baz>[^/]+))?$'),
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
        self.router.add('/', None)

        def a(): pass
        self.router.add('/foo', a)

        def b(foo): pass
        self.router.add('/:foo', b)

        def c(foo, bar): pass
        self.router.add('/:foo/:bar', c)

        def d(foo, bar=None): pass
        self.router.add('/:foo[/:bar]', d)

        def e(): pass
        self.router.add('/', e, methods='POST')

        self.assertNotEqual(self.router.urls['GET'], {})
        self.assertNotEqual(self.router.urls['POST'], {})

        self.assertTrue('/:foo' in [item.route for regex, item in self.router.urls['GET'].iteritems()])
        self.assertTrue('/' in [item.route for regex, item in self.router.urls['GET'].iteritems()])
        self.assertTrue('/' in [item.route for regex, item in self.router.urls['POST'].iteritems()])

    def it_should_add_complex_routes(self):
        self.router.add(r'^/$', None)

        def foo(): pass
        self.router.add(r'^/index$', foo)
        self.router.add(r'^/(index)?', foo, methods='GET, POST')

        def bar(foo, bar, baz): pass
        self.router.add(r'^/(?P<foo>[^/]+)/(?P<bar>[^/]+)(/(?P<baz>[^/]+))?$', bar)

        self.assertNotEqual(self.router.urls['GET'], {})
        self.assertNotEqual(self.router.urls['POST'], {})

        self.assertTrue(r'^/index$' in [item.route for regex, item in self.router.urls['GET'].iteritems()])
        self.assertTrue(r'^/(index)?' in [item.route for regex, item in self.router.urls['GET'].iteritems()])
        self.assertTrue(r'^/(index)?' in [item.route for regex, item in self.router.urls['POST'].iteritems()])

    def it_should_find_simple_routes(self):

        routes = (
            # route, search, match, method, func
            ('/', '/', '/', 'GET', None),
            ('/index', '/index', '/index', 'POST', None),
            )

        for route, search, match, method, func in routes:
            self.router.add(route, func, methods=method)

            item, params = self.router.find(method, search)

            self.assertEqual(item.route, match)
            self.assertEqual(item._callable, func)
        
    def it_should_find_a_simple_route_with_optional_params(self):

        def a():pass
        def b():pass

        routes = (
            ('/[index]', '/', 'GET', a),
            ('/', '/', 'GET', b),
            )

        for route, test, method, func in routes:
            self.router.add(route, func, methods=method)

        item, params = self.router.find('GET', '/')
        print item, params

        self.assertEqual(item.route, '/[index]')
        self.assertEqual(item._callable, a)
        
    def it_should_find_simple_parameters(self):

        def a(foo): pass
        def b(bar): pass
        def c(foo, bar): pass
        
        routes = (
            ('/:foo', '/meh', {'foo': 'meh'}, 'GET', a),
            ('/foo/:bar', '/foo/meh', {'bar': 'meh'}, 'GET', b),
            ('/:foo/:bar', '/bur/meh', {'foo': 'bur', 'bar': 'meh'}, 'GET', c),
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

    def it_should_return_NotFound_for_unmatched_routes(self):
        self.assertRaises(NotFound,
                          self.router.find,
                          'GET',
                          '/')
        

    def _test_routes(self, routes):
        for route, test, params, method, func in routes:
            self.router.add(route, func, methods=method)

            #print self.router.urls['GET']

            item, params_ = self.router.find(method, test)

            self.assertEqual(item.route, route)
            self.assertEqual(item._callable, func)
            self.assertEqual(params_, params)
            
    def _patterns_should_equal(self, patterns):
        for route, result in patterns:
            pattern, regex = Route._compile_regex(route)
            self.assertEqual(type(pattern), re._pattern_type)
            self.assertEqual(regex, result)
            
    def _patterns_should_raise(self, patterns, exception=Exception):
        for route in patterns:
            self.assertRaises(exception,
                              Route._compile_regex,
                              route)

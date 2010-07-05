Still To Do
===========

- Unittests
- Documentation
- Relative imports for XSL Documents
- Lazy-loading/-parsing of request parameters; test whether a method expects args?
- Handle objects correctly in XML/JSON Translations
- sessions from `beaker`_, with local fall-back?
- auto-reload of modules, etc.
- `XSRF`_ validation, similar to that from `tornado`_
- Documentation
- Tests
- setup.py for distribution
- seaside-based form handling
- decorator for storing function return value in session -- memoize
- InternalRedirect exception to restart the request with new data but respond to original query:
  - InteralRedirect(url, method='GET', params={}, replace_params=False)
- Parameter object for working with both string and native parameters
- base64 encoding of binary data in JSON output, using the data-uri format.

- Optional items:
  - Handle ``func=None`` in routing as pass-through/file-read
  - Add ``sendfile`` func which is compatible with Nginx X-Accel headers
  - XML: allow creating of processing instructions using the following format: ``{"?xml-stylesheet": {'type':'', 'href':''}} ``

- `XPath Callbacks`_ to the framework from XSL; 
  - [DONE] fwrd:param('name', 'type'?)
  - fwrd:call('url', 'params', 'method=GET')
  - [DONE] fwrd:config('name')
  - fwrd:session('n')
  - [DONE,UNNEEDED?] fwrd:environ('n')

- XPath functions:
  - abs
  - ceiling
  - floor
  - avg
  - min
  - max
  - round
  - roundhalftoeven
  - compare
  - any(test, (els))?
  - all(test, (els))?
  - --coalesce--
  - concat
  - --join--
  - implode
  - --upper--
  - --lower--
  - in
  - startswith
  - endswith
  - matches
  - replace
  - tokenize
  - empty
  - exists?
  - distinct (values)
  - unique (nodes)
  - reverse
  - --dateformat--
  - --timeformat--

- Decorators:
  - @fwrd.use.formatter('name'); change default formatter for function
  - @fwrd.use.stylesheet('path/to/xsl'); force use of stylesheet
  - @fwrd.req.formatter('name'); force formatter for all output

- [UNNEEDED?] ``define`` and ``defined``, from `tornado`_.
- [DONE] Handle dates correctly in XML/JSON Translations
- [DONE] Enhance routing with conditional elements ``/[index]``
- [DONE] Correct HTTP Method handling in routing
- [DONE] Fix ``run`` method
- [DONE] Correct handling of ValueError
- [DONE] Registration methods for formatters, middleware
- [DONE] correct 404/500 error handling
- [DONE] correct redirect handling
- [DONE] reproduce `bottle`_'s ``cast`` method; it's a great idea, and could be handy for output types.
- [DONE] better mapping of request variables, following PHP's GPCS over-writing model but allowing access to original values, similar to `webob`_.
- [DONE] Response headers to be handled by ``wsgiref.headers.headers``
- [DONE] Correct handling of threading with request/response objects
- [DONE] XSL formatting of output
- [DONE] Better handling of output through XSL

TBC
---

Simple sessions which are overridden by beaker?

How should authentication be handled? `AuthKit`_? Custom?

Memoization of "compiled" XSL?

``@fwrd.validate.param('param_name', using=MyValidatorFunc)`` decorator?

Keep a log of the last request's (or last few requests'?) information (request, params, session, etc) to be raised when an error/exception is thrown.

.. _tornado: http://github.com/facebook/tornado
.. _beaker: http://beaker.groovie.org
.. _AuthKit: http://authkit.org
.. _webob: http://pythonpaste.org/webob
.. _bottle: http://github.com/defnull/bottle
.. _XPath Callbacks: http://codespeak.net/lxml/extensions.html#xpath-extension-functions
.. _XSRF: http://en.wikipedia.org/wiki/Cross-site_request_forgery

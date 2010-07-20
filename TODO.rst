Still To Do
===========

- Documentation

- Testing
  - Specs for middleware

- Features
  - Subrequest method for internal request, with formatting
  - Inspection of methods to ascertain whether they need arguments *before* being called
  - Local fall-back for sessions when beaker isn't available
  - Auto-reloading of code on file modification
  - `XSRF`_ validation, similar to that from `tornado`_
  - seaside-based form handling: 
    - each browser tab can have/has it's own session
    - forms can be secured with unique key in "action" url
  - auto-creation of caching decorator when beaker-cache is available
  - InternalRedirect exception to restart the request with new data but respond to original query:
    - InteralRedirect(url, method='GET', params={}, replace_params=False)
  - Parameter "type" for working with both string and native parameters
  - base64 encoding of binary data in JSON output, using the data-uri format.

- Optional features:
  - Add ``sendfile`` func which is compatible with Nginx X-Accel headers
  - XML: allow creating of processing instructions using the following format: ``{"?xml-stylesheet": {'type':'', 'href':''}} ``

  - `XPath Callbacks`_ to the framework from XSL; 
    - fwrd:subrequest('url', 'params', 'method=GET')
    - fwrd:session('n')

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
    - concat
    - implode
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

  - Decorators:
    - @response.format('type', **params); change default formatter for function

  - ``define`` and ``defined``, from `tornado`_.

TBC
---

How should authentication be handled? `AuthKit`_? Custom?

Memoization of "compiled" XSL?

Keep a log of the last request's (or last few requests'?) information (request, params, session, etc) to be raised when an error/exception is thrown.

.. _tornado: http://github.com/facebook/tornado
.. _beaker: http://beaker.groovie.org
.. _AuthKit: http://authkit.org
.. _webob: http://pythonpaste.org/webob
.. _bottle: http://github.com/defnull/bottle
.. _XPath Callbacks: http://codespeak.net/lxml/extensions.html#xpath-extension-functions
.. _XSRF: http://en.wikipedia.org/wiki/Cross-site_request_forgery

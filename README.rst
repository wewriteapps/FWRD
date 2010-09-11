::

   _______ ________ ______ _____  
  |    ___|  |  |  |   __ \     \ 
  |    ___|  |  |  |      <  --  |
  |___|   |________|___|__|_____/ 
  

FWRD -- FrameWork, Re-Done
==========================

DESCRIPTION
-----------

FWRD is a microframework for Python designed to 
"get out of the way" and only provide what's 
really needed.

FWRD is still alpha software. Until it hits version
1.0 the api is subject to massive change/overhaul.

FEATURES
--------

- WSGI-compliant

- Simple routing with URL parameters

- HTTP Method support for the "useful" methods: GET/POST/PUT/DELETE/HEAD

- Redirect support

- Automatic Response formatting (XML, JSON, YAML, more to follow)

NOT IMPLEMENTED
---------------

Templating
    We don't support templating using any of the common Python templating 
    libraries (Jinja, Cheetah, Mako, etc). It's XSL or nothing with FWRD.
    And that's the point - FWRD's default output is XML, but you can define
    the output to be JSON, YAML, etc. without any "work". A templating 
    language would just "get in the way".

ORM
    We don't feel that we should dictate what database you use, so we don't
    supply an ORM. Feel free to use any of the popular ones, or an ODM, or 
    a flat-file database, or an in-memory database, or whatever persistance 
    you wish!

INSTALLATION
------------

Currently FWRD is alpha software. Until there are official releases please
install from the master:

    pip install http://github.com/digitala/FWRD/zipball/master

USAGE
-----
::

    from FWRD import *
    
    def hello_world(name='World'):
        return 'Hello %s!' % name

    router.urls = (
        ('/[index]', None),
	('/hello[/:world]', hello_world),
	)

    application.run()

PLANNED FEATURES / TO DO
------------------------

Please see the TODO_ document.

DEPENDENCIES
------------

- specloud_ (for running specs/tests)

.. _TODO: //github.com/digitala/FWRD/blob/master/TODO.rst
.. _specloud: //github.com/hugobr/specloud

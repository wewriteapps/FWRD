::

   _______ ________ ______ _____  
  |    ___|  |  |  |   __ \     \ 
  |    ___|  |  |  |      <  --  |
  |___|   |________|___|__|_____/ 
  

FWRD -- FrameWork, Re-Done
==========================

DESCRIPTION
-----------

FWRD is a microframework for Python which has been designed to 
"get out of the way" and only provide enough to make an app
accessible from the web.

FWRD is still alpha software. Until it hits version
1.0 the api is subject to massive change/overhaul.

FEATURES
--------

- WSGI-compliant

- Simple routing with URL parameters

- HTTP Method support for the "useful" methods: GET/POST/PUT/DELETE/HEAD

- Redirect support

- Automatic Response formatting: XSL-Translated output, XML, JSON (more to follow)

THINGS WE HAVEN'T IMPLEMENTED
-----------------------------

Templating
    We don't support templating using any of the common Python templating 
    libraries such as Jinja, Cheetah, Mako, etc. The default output format 
    is XML passed through an XSL stylesheet. Helpful formatters are available 
    so you can change the output to be JSON, YAML, etc. without any extra 
    "work"; just let your method return it's results and it will be converted 
    to something useful. 

    However, if you really need to use an alternative formatter you can do
    so by creating a "plugin" for the ``Response``.

ORM
    We don't feel that we should dictate what database you use, so we don't
    supply an ORM. Feel free to use any of the popular ones, or an ODM, or 
    a flat-file database, or an in-memory database, or whatever persistance 
    you wish.

INSTALLATION
------------

Currently FWRD is alpha software. Until there are official releases please
install from the master:

    pip install http://github.com/digitala/FWRD/tarball/master

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

.. _TODO: //github.com/digitala/FWRD/blob/master/TODO.rst

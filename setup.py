from setuptools import setup, find_packages
import sys

execfile('FWRD/__version__.py')

setup(name="FWRD",
      version=__version__,
      url="http://github.com/digitala/FWRD",
      packages=find_packages(exclude="specs"),
      install_requires=['lxml', 'simplejson', 'iso8601', 'Beaker', 'PyYAML', 'resolver', 'ordereddict'],
      )
      

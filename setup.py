from setuptools import setup, find_packages
import sys

setup(name="FWRD",
      version="0.2",
      url="http://github.com/digitala/FWRD",
      packages=find_packages(exclude="specs"),
      install_requires=['lxml', 'simplejson', 'iso8601', 'Beaker', 'PyYAML'],
      )
      

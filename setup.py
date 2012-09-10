from setuptools import setup, find_packages
import os, sys

execfile('FWRD/__version__.py')

# http://peak.telecommunity.com/DevCenter/setuptools#dependencies-that-aren-t-in-pypi

setup(name="FWRD",
      description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
      version=__version__,
      url="http://github.com/unpluggd/FWRD",
      packages=find_packages(exclude="specs"),
      install_requires=[
          'exemelopy',
          'lxml',
          'simplejson',
          'Beaker',
          'PyYAML',
          'resolver',
          'ordereddict',
          'PySO8601',
          'pytz',
          ],
      )


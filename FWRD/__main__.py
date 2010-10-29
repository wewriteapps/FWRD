import sys
from optparse import OptionParser

EXAMPLE_CONFIG = '''## This is an example configuration file for a FWRD web application
## in standard YAML () format.
## For more information on options please see the docs.

Config:
  port: 8001 

Formats:
  default: XSL
  XSL:
    enabled: Yes
    stylesheet_path: xsl
    default_stylesheet: default.xsl
  XML:
    enabled: Yes
  JSON:
    enabled: Yes

Routes:
  - route: /[index]
    callable: None # must be available from the main script
    methods: [GET, POST] # GET by default
    filters: [] # a list of callables 
    formats: [XSL,XML,JSON] # All enabled formatters are allowed by default; use this list to override

'''

#if __name__ == '__main__':
parser = OptionParser()
parser.add_option('-n', '--new-config',
                  dest='export_example_config',
                  action='store_true',
                  help='This will print a "sample" configuration file to your terminal\'s stdout')

(options, args) = parser.parse_args()

if options.export_example_config:
    print EXAMPLE_CONFIG
    raise SystemExit()

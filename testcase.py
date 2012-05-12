import unittest
import logging

logging.basicConfig(level=logging.DEBUG)

from lxml import etree


def has_nodes(context, nodes):
    return nodes != []


class XPathFunctionTestCase(unittest.TestCase):
    def setUp(self):
        ns = etree.FunctionNamespace('http://lxml.de/test-cases')
        ns.prefix = 'test'
        ns['has-nodes'] = has_nodes

        self.xml = etree.fromstring('''<?xml version="1.0" encoding="UTF-8"?><a><b><c>example</c></b></a>''')

        self.xsl = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:test="http://lxml.de/test-cases"
  exclude-result-prefixes="test">
<xsl:output method="html" />
<xsl:template match="/">
<html><body><xsl:if test="test:has-nodes(%s)">yes</xsl:if></body></html>
</xsl:template>
</xsl:stylesheet>
'''


    def test_has_nodes_using_node_name(self):
        result = etree.XSLT(etree.fromstring(self.xsl % 'a')).apply(self.xml)
        self.assertEqual(str(result),
                         '<html><body>yes</body></html>\n')


    def test_has_nodes_using_self(self):
        result = etree.XSLT(etree.fromstring(self.xsl % 'self')).apply(self.xml)
        self.assertEqual(str(result),
                         '<html><body>yes</body></html>\n')


    def test_has_nodes_using_self_shortcut(self):
        result = etree.XSLT(etree.fromstring(self.xsl % '.')).apply(self.xml)
        self.assertEqual(str(result),
                         '<html><body>yes</body></html>\n')


    def test_has_nodes_using_self_node(self):
        result = etree.XSLT(etree.fromstring(self.xsl % 'self::node()')).apply(self.xml)
        self.assertEqual(str(result),
                         '<html><body>yes</body></html>\n')


    def test_has_nodes_using_current(self):
        result = etree.XSLT(etree.fromstring(self.xsl % 'current()')).apply(self.xml)
        self.assertEqual(str(result),
                         '<html><body>yes</body></html>\n')



if __name__ == '__main__':
    unittest.main()

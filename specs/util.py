from lxml import etree

def assert_xpath(self, tree, xpath, value, ns=None):

    if ns:
        results = tree.xpath(xpath, namespaces=ns, smart_strings=False)
    else:
        results = tree.xpath(xpath, smart_strings=False)

    if not results:
        self.fail("XPath '%s' produced no results" % xpath)


    if value is None:
        def test(result, *args, **kwargs):
            self.assertEqual(result, None)

    elif isinstance(value, basestring):
        def test(result, *args, **kwargs):
            self.assertEqual(result, value)

    elif isinstance(value, (tuple, list, set)):
        def test(result, i, *args, **kwargs):
            self.assertEqual(result, value[i])

    elif isinstance(value, dict):
        def test(result, *args, **kwargs):
            self.assertEqual(result, value[result.tag])

    else:
        self.fail("value is not a usable type")


    for i, result in enumerate(results):
        if hasattr(result, 'text'):
            text = result.text
        else:
            text = result
        test(text, i)


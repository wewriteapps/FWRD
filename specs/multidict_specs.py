import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

#from FWRD import MultiDict

"""
class MultiDictSpec(unittest.TestCase):

    def setUp(self):
        self.dict = MultiDict()

    def it_should_accept_items_at_init(self):
        pass
        
    def it_should_accept_new_items(self):
        pass

    def it_should_delete_items(self):
        pass

    def it_should_clear_all_items(self):
        pass

    def it_should_set_and_get_multiple_items_with_the_same_key(self):
        pass

    def it_should_show_correct_length(self):
        pass
"""

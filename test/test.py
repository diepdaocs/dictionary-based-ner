import unittest

from dictionary import DictionaryES
from pprint import pprint

from text_stats import TextStats


class MyTestCase(unittest.TestCase):
    def test_add_vocs(self):
        d = DictionaryES()
        d.add_voc(['new york', 'Chicago', 'San Francisco', 'Lisbonk', 'Portugal',
                   'Mumbai', 'Cochin', 'Kolkata', 'Beijing', 'Shanghai', 'NY'], 'city')
        d.add_voc(['black', 'white', 'yellow', 'red', 'green', 'blue', 'orange'], 'color')

    def test_get_vocs(self):
        d = DictionaryES()
        pprint(d.get_voc([]))

    def test_tag_texts(self):
        d = DictionaryES()
        res = d.tag(['hotel in chicAgo rEd', 'food in Ha    nOi'], ['city', 'color'])
        pprint(res)

    def test_stats(self):
        stats = TextStats()
        ret = stats.get_stats(['hotel in chicAgo', 'food in Ha    nOi', 'blue skype in ho chi minh city'], ' ', '')
        pprint(ret)


if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-
import unittest

from dictionary import DictionaryES
from pprint import pprint

from text_stats import TextStats
from util.utils import get_logger


class MyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MyTestCase, self).__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)

    def test_add_vocs(self):
        d = DictionaryES()
        d.add_voc(['new york', 'Chicago', 'San Francisco', 'Lisbonk', 'Portugal',
                   'Mumbai', 'Cochin', 'Kolkata', 'Beijing', 'Shanghai', 'NY'], 'city', 'english')
        d.add_voc(['black', 'white', 'yellow', 'red', 'green', 'blue', 'orange'], 'color', 'english')
        d.add_voc(['Schwarz', 'weiß', "gelb", "rot", "grün", "blau", "Orange"], 'color', 'german')
        d.add_voc(['Schwarz', 'weiß', "gelb", "rot", "grün", "blau", "Orange"], 'color', 'abc')

    def test_get_vocs(self):
        d = DictionaryES()
        pprint(d.get_voc(['city'], 'english'))

    def test_remove_vocs(self):
        d = DictionaryES()
        d.remove_voc('city', ['new york', 'Schwarz'], 'english')

    def test_delete_dic(self):
        d = DictionaryES()
        res = d.remove_dic(['color'], 'english')
        self.logger.debug(res)

    def test_tag_texts(self):
        d = DictionaryES()
        res = d.tag(['hotel in chicAgo', 'a beautiful blue (blau) sky green', 'blue sky in beijing'], ['city', 'color'],
                    'english')
        self.logger.info(res)

    def test_stats(self):
        stats = TextStats()
        ret = stats.get_stats(['hotel in chicAgo', 'a beautiful blue (blau) sky green', 'blue sky in beijing'], ' ', '', 'english')
        self.logger.info(ret)


if __name__ == '__main__':
    unittest.main()

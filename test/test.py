# -*- coding: utf-8 -*-
import json
import unittest

import time

from dictionary import DictionaryES
from pprint import pprint

from text_stats import TextStats
from util.utils import get_logger


class MyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MyTestCase, self).__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)

    def test_add_vocs(self):
        self.logger.info('Run test case: %s', 'test_add_vocs')
        d = DictionaryES()
        d.es.indices.delete('_all')
        d.add_voc(['new york', 'Chicago', 'San Francisco', 'Lisbonk', 'Portugal',
                   'Mumbai', 'Cochin', 'Kolkata', 'Beijing', 'Shanghai', 'NY'], 'city', 'english')
        d.add_voc(['black', 'white', 'yellow', 'red', 'green', 'blue', 'orange'], 'color', 'english')
        d.add_voc(['Schwarz', 'weiß', "gelb", "rot", "grün", "blau", "Orange"], 'color', 'german')
        d.add_voc(['Schwarz', 'weiß', "gelb", "rot", "grün", "blau", "Orange"], 'color', 'abc')
        self.assertTrue(d.get_voc(['city'], 'english') > 0)

    def test_get_vocs(self):
        self.logger.info('Run test case: %s', 'test_get_vocs')
        d = DictionaryES()
        res = d.get_voc(['city'], 'english')
        pprint(res)
        self.assertTrue(res[0]['num_voc'] > 0)

    def test_remove_vocs(self):
        self.logger.info('Run test case: %s', 'test_remove_vocs')
        d = DictionaryES()
        nv_before = d.get_voc(['city'], 'english')[0]['num_voc']
        success, fail = d.remove_voc('city', ['Schwarz'], 'english')
        after = d.get_voc(['city'], 'english')[0]
        nv_after = after['num_voc']
        self.assertNotIn('Schwarz', after['vocs'])
        self.assertEqual(nv_before - success, nv_after)

    def test_delete_dic(self):
        self.logger.info('Run test case: %s', 'test_delete_dic')
        d = DictionaryES()
        res = d.remove_dic(['color'], 'abc')
        self.logger.debug(res)
        self.assertEqual(len(d.get_voc(['color'], 'abc')), 0)

    def test_tag_texts(self):
        self.logger.info('Run test case: %s', 'test_tag_texts')
        d = DictionaryES()
        res = d.tag(['orange hotel in chicAgo', 'a beautiful blue (blau) sky green', 'blue sky in beijing'],
                    ['city', 'color'],
                    'english', match_type='broad')
        self.logger.info(res)
        self.assertEqual(res[0]['norm_text'], '[color] hotel in [city]')
        self.assertEqual(res[1]['norm_text'], 'a beautiful [color] (blau) sky [color]')
        self.assertEqual(res[2]['norm_text'], '[color] sky in [city]')

    def test_stats(self):
        self.logger.info('Run test case: %s', 'test_stats')
        stats = TextStats()
        res = stats.get_stats(['hotel in chicAgO'], 'o', '', 'english')
        self.logger.info(json.dumps(res))
        self.assertEqual(res[0]['num_char'], 16)
        self.assertEqual(res[0]['num_word'], 3)
        self.assertEqual(res[0]['num_count_only'], 2)
        self.assertEqual(res[0]['norm_text'], 'hotel in [city]')
        self.assertEqual(len(res[0]['tag']), 1)

    def test_broad_match(self):
        self.logger.info('Run test case: %s', 'test_broad_match')
        stats = TextStats()
        res = stats.get_stats(['hotel in new york', 'hotel in newyork', 'hotel in newyoork', 'hotel in neu york',
                               'hotel in ne york'], ' ', '', 'english')
        self.logger.info(json.dumps(res))
        for t in res:
            pprint(t)
            self.assertEqual(len(t['tag']), 1)
            self.assertEqual(t['norm_text'], 'hotel in [city]')

    def test_exact_match(self):
        self.logger.info('Run test case: %s', 'test_exact_match')
        stats = TextStats()
        res = stats.get_stats(['hotel in new york', 'hotel in newyork', 'hotel in newyoork', 'hotel in neu york',
                               'hotel in ne york', 'blues sky in chicage'], ' ', '', 'english', match_type='exact')
        self.logger.info(json.dumps(res))
        print json.dumps(res[0])
        self.assertEqual(len(res[0]['tag']), 1)
        self.assertEqual(res[0]['norm_text'], 'hotel in [city]')
        for t in res[1:]:
            pprint(t)
            self.assertEqual(len(t['tag']), 0)


if __name__ == '__main__':
    unittest.main()

import re

from dictionary import DictionaryES
from tokenizer import GeneralTokenizer
from util.utils import get_logger


class TextStats(object):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.tokenizer = GeneralTokenizer()
        self.url_pattern = re.compile(r'(?:http[s]?://|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.dictionary = DictionaryES()

    def _count_word(self, text):
        text = self.url_pattern.sub('[url]', text)
        return len(self.tokenizer.tokenize(text))

    def _get_type(self, text):
        text_type = 'word'
        urls = self.url_pattern.findall(text)
        if urls and len(urls) == 1 and len(urls[0]) == len(text):
            text_type = 'url'
        elif urls and len(urls[0]) != len(text):
            text_type = 'mixed'

        return text_type

    def get_stats(self, texts, count_only, lookup, lang):
        result = []
        # basic stats
        for text in texts:
            result.append({
                'text': text,
                'num_word': self._count_word(text),
                'num_char': len(text),
                'num_count_only': text.lower().count(count_only.lower()) if count_only else 0,
                'type': self._get_type(text)
            })

        # named entity tagging
        tags = self.dictionary.tag(texts, lookup, lang)

        for idx, tag in enumerate(tags):
            result[idx]['norm_text'] = tag['norm_text']
            result[idx]['tag'] = tag['tag']

        return result

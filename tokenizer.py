import string
from abc import ABCMeta, abstractmethod
from nltk import wordpunct_tokenize


class Tokenizer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def tokenize(self, text):
        pass


class GeneralTokenizer(Tokenizer):

    def normalize(self, text):
        return ' '.join(self.tokenize(text))

    def tokenize(self, text):
        result = []
        if type(text) is not unicode:
            text = unicode(text, 'utf-8', errors='ignore')

        # pre tokenize
        for word in wordpunct_tokenize(text):
            word = word.strip(string.punctuation).lower()
            if word:
                result.append(word)
        return result

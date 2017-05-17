import logging
from abc import abstractmethod, ABCMeta
import re

import time
from elasticsearch import TransportError
from elasticsearch.helpers import bulk, scan
from multiprocessing import cpu_count

from util.database import get_es_client
from util.utils import get_logger, get_unicode, chunks
import Levenshtein
from multiprocessing.dummy import Pool


class Dictionary(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_voc(self, vocs, dic, lang):
        pass

    @abstractmethod
    def get_voc(self, dics, lang):
        pass

    @abstractmethod
    def tag(self, texts, dics, lang, match_type):
        pass

    @staticmethod
    def _normalize(text):
        return re.sub(r'\s+', ' ', get_unicode(text).strip().lower())


def get_ngram(text_tokens, max_gram, min_ngram=1):
    result = set()
    tokens_len = len(text_tokens)
    for i in range(min_ngram, max_gram + 1):
        for k in range(tokens_len - i + 1):
            text = ' '.join(text_tokens[k: k + i])
            result.add(text)

    return list(result)


class DictionaryES(Dictionary):
    MATCH_TYPE_BROAD = 'broad'
    MATCH_TYPE_EXACT = 'exact'

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.es = get_es_client()
        self.prefix_index_name = 'dic'
        self.doc_type = 'vocab'
        self.support_languages = {'arabic', 'armenian', 'basque', 'brazilian', 'bulgarian', 'catalan', 'cjk', 'czech',
                                  'danish', 'dutch', 'english', 'finnish', 'french', 'galician', 'german', 'greek',
                                  'hindi',
                                  'hungarian', 'indonesian', 'irish', 'italian', 'latvian', 'lithuanian', 'norwegian',
                                  'persian',
                                  'portuguese', 'romanian', 'russian', 'sorani', 'spanish', 'swedish', 'turkish',
                                  'thai'}
        self.thread_num = cpu_count() * 2
        logging.getLogger('elasticsearch').setLevel(logging.CRITICAL)

    def _get_index_list_str(self, dics, lang):
        if not dics:
            return '%s-*-%s' % (self.prefix_index_name, lang)
        index_list = [self._get_index_name(dic, lang) for dic in dics]
        # filter non-exists indices
        index_list = [idx for idx in index_list if self.es.indices.exists(idx)]
        return ','.join(index_list)

    def _get_tag_info(self, (text, lang, dics, index_name, match_type)):
        n_text = self._normalize(text)
        if match_type == self.MATCH_TYPE_BROAD:
            query = {
                'query': {
                    'multi_match': {
                        'fields': ['voc', 'voc_ngram'],
                        'query': n_text,
                        'fuzziness': 'AUTO',
                        'analyzer': lang,
                        'prefix_length': 3,
                        'max_expansions': 5
                    }
                }
            }
        else:
            query = {
                'query': {
                    'match': {
                        'voc': n_text
                    }
                }
            }

        query['size'] = 100
        hits = self.es.search(index=index_name, doc_type=self.doc_type, body=query)['hits']['hits']
        tag_voc = {}
        text_tokens = None
        text_ngram = None
        if '*' not in index_name and ',' not in index_name:
            # only 1 index case
            text_tokens = self._get_text_tokens(n_text, index_name)
            n_text = ' '.join(text_tokens)
            text_ngram = get_ngram(text_tokens, len(text_tokens))
        try:
            for hit in hits:
                doc = hit['_source']
                voc = doc['voc']
                if text_tokens is None:
                    # multi index case
                    text_tokens = self._get_text_tokens(n_text, hit['_index'])
                    n_text = ' '.join(text_tokens)
                    text_ngram = get_ngram(text_tokens, len(text_tokens))

                n_voc = ' '.join(self._get_text_tokens(voc, hit['_index']))
                match_token = self._fuzzy_matching(text_ngram, n_voc) if match_type == self.MATCH_TYPE_BROAD \
                    else self._exact_matching(text_ngram, n_voc)
                if not match_token:
                    continue
                pattern = re.compile(r'\b(%s)\b' % match_token, re.IGNORECASE)
                dic = hit['_index'].split('-')[1]
                if dic in tag_voc:
                    tag_voc[dic]['matches'].add((match_token, voc))
                    tag_voc[dic]['count'] += 1
                else:
                    tag_voc[dic] = {'matches': {(match_token, voc)}, 'count': 1}

                n_text = pattern.sub('[' + dic + ']', n_text)

        except TransportError as ex:
            self.logger.error('index not found: %s' % ex.message)

        # convert set to list for json serialize
        for t in tag_voc:
            tag_voc[t]['matches'] = list(tag_voc[t]['matches'])

        # append empty tag
        for dic in dics:
            if dic not in tag_voc:
                tag_voc[dic] = {'count': 0, 'matches': []}

        return {
            'norm_text': n_text,
            'tag': tag_voc
        }

    def tag(self, texts, dics, lang, match_type):
        self.logger.info("Start tag %s texts by %s in %s language..." % (len(texts), dics, lang))
        index_name = self._get_index_list_str(dics, lang)
        if not index_name:
            return []
        if len(texts) < 10:
            return [self._get_tag_info((text, lang, dics, index_name, match_type)) for text in texts]

        pool = Pool(self.thread_num)
        result = pool.map(self._get_tag_info, [(text, lang, dics, index_name, match_type) for text in texts])
        pool.terminate()
        return result

    def get_voc(self, dics, lang):
        result = []
        index_name = self._get_index_list_str(dics, lang)
        if not index_name:
            return []
        dic_vocs = {}
        query = {
            'query': {
                'match_all': {}
            }
        }
        hits = scan(client=self.es, index=index_name, doc_type=self.doc_type, query=query)
        try:
            for hit in hits:
                dic_name = hit['_index'].split('-')[1]
                doc = hit['_source']
                if dic_name in dic_vocs:
                    dic_vocs[dic_name].append(doc['voc'])
                else:
                    dic_vocs[dic_name] = [doc['voc']]
        except TransportError as ex:
            self.logger.error('index not found: %s' % ex.message)

        for dic, vocs in dic_vocs.items():
            result.append({
                'dic': dic,
                'num_voc': len(vocs),
                'vocs': vocs
            })

        return result

    def remove_dic(self, dics, lang):
        result = []
        for dic in dics:
            error = ''
            index_name = self._get_index_name(dic, lang)
            try:
                if self.es.indices.exists(index_name):
                    self.es.indices.delete(index_name)
                    self.logger.info('Delete dictionary %s successfully' % dic)
                else:
                    error = "Dictionary '%s' does not exist" % dic
            except Exception as ex:
                self.logger.info('Remove dictionary error: %s' % ex.message)
                error = ex.message

            result.append({
                'dic': dic,
                'error': True if error else False,
                'message': error if error else 'Dictionary was removed successfully'
            })

        return result

    def remove_voc(self, dic, vocs, lang):
        index_name = self._get_index_name(dic, lang)
        vocs = [self._normalize(v) for v in vocs]
        vocs = self._get_exist_voc(vocs, index_name, self.doc_type)
        if not vocs:
            self.logger.info('All vocabularies has been removed')
            return 0, 0

        delete_actions = []
        for voc in vocs:
            delete_actions.append({
                '_op_type': 'delete',
                '_index': index_name,
                '_type': self.doc_type,
                '_id': voc
            })
        stats = bulk(self.es, delete_actions, stats_only=True, refresh=True)
        self.logger.info('Delete Success/Fail: %s/%s' % stats)
        return stats

    def _get_exist_voc(self, vocs, index_name, doc_type):
        # get existed vocabulary
        existed_voc = set()
        query = {
            'query': {
                'filtered': {
                    'filter': {
                        'terms': {
                            '_id': vocs
                        }
                    }
                }
            }
        }
        hits = scan(client=self.es, query=query, index=index_name, doc_type=doc_type)
        for hit in hits:
            existed_voc.add(get_unicode(hit['_source']['voc']))

        return existed_voc

    def add_voc(self, vocs, dic, lang):
        self.logger.info('Start add %s vocs for %s in %s language...' % (len(vocs), dic, lang))
        index_name = self._get_index_name(dic, lang)
        first_init = False
        # check exist index
        if not self.es.indices.exists(index_name):
            first_init = True
            # create index
            self.logger.info('Create new index: ' + index_name)
            body = {
                'mappings': {
                    self.doc_type: {
                        'properties': {
                            'voc': {
                                'type': 'string',
                                'analyzer': lang if lang in self.support_languages else 'standard'
                            },
                            'voc_ngram': {
                                'type': 'string',
                                'analyzer': 'keyword'
                            }
                        }
                    }
                },
                'settings': {
                    'index': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0
                    }
                }
            }
            self.es.indices.create(index_name, body=body)
            sleep = 1
            self.logger.info('Sleep %s seconds for index to be available' % sleep)
            time.sleep(sleep)

        # normalize vocabularies
        vocs = [self._normalize(v) for v in vocs]

        # check exist vocs
        if not first_init:
            existed_voc = self._get_exist_voc(vocs, index_name, self.doc_type)
            self.logger.debug('Num of existed vocs: %s' % len(existed_voc))
            vocs = [v for v in vocs if v not in existed_voc]

        if not vocs:
            self.logger.info('All vocabularies has been added')
            return 0, 0

        self.logger.debug('Num of remained vocs: %s' % len(vocs))

        index_actions = []
        for voc in vocs:
            text_tokens = self._get_text_tokens(voc, index_name)
            index_actions.append({
                '_op_type': 'index',
                '_index': index_name,
                '_type': self.doc_type,
                '_id': voc,
                '_source': {
                    'voc': voc,
                    'voc_ngram': get_ngram(text_tokens, max_gram=len(text_tokens), min_ngram=2)
                }
            })
        if index_actions < 1000:
            stats = bulk(self.es, index_actions, stats_only=True, refresh=True)
            self.logger.info('Index Success/Fail: %s/%s' % stats)
            self.logger.info('End add_voc...')
            return stats

        pool = Pool(8)
        stats = pool.map(self._bulk_index, [chunk for chunk in chunks(index_actions, 1000)])
        pool.terminate()

        success, fail = 0, 0
        for s in stats:
            success += s[0]
            fail += s[1]

        return success, fail

    def _bulk_index(self, index_actions):
        stats = bulk(self.es, index_actions, stats_only=True, refresh=True)
        self.logger.info('Index Success/Fail: %s/%s' % stats)
        return stats

    def _get_index_name(self, dic, lang):
        return '%s-%s-%s' % (self.prefix_index_name, dic, lang)

    @staticmethod
    def _fuzzy_matching(text_ngram, c_text):
        matches = {}
        c_text = c_text.lower()
        for token in text_ngram:
            token = token.lower()
            if token[0:2] != c_text[0:2]:
                continue

            t_len = len(token)

            if 0 <= t_len <= 3:
                if token == c_text:
                    return token
            elif 4 <= t_len <= 5:
                edit = Levenshtein.distance(token, c_text)
                if edit <= 1:
                    matches[edit] = token
            else:
                edit = Levenshtein.distance(token, c_text)
                if edit <= 2:
                    matches[edit] = token
        if not matches:
            return False
        return matches[min(matches.keys())]

    @staticmethod
    def _exact_matching(text_ngram, c_text):
        c_text = c_text.strip().lower()
        for token in text_ngram:
            token = token.strip().lower()
            if token == c_text:
                return token

        return False

    def _get_text_tokens(self, n_text, index_name):
        # body = {
        #     'field': 'voc',
        #     'text': n_text
        # }
        # tokens = self.es.indices.analyze(index_name, body)['tokens']
        # return [t['token'] for t in tokens]
        return [t.strip() for t in n_text.split() if t and t.strip()]



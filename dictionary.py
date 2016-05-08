import logging
from abc import abstractmethod, ABCMeta
import re

from elasticsearch import NotFoundError, TransportError
from elasticsearch.helpers import bulk, scan
from util.database import get_es_client
from util.utils import get_logger, get_unicode


class Dictionary(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_voc(self, vocs, dic, lang):
        pass

    @abstractmethod
    def get_voc(self, dics, lang):
        pass

    @abstractmethod
    def tag(self, texts, dics, lang):
        pass

    @staticmethod
    def _normalize(text):
        return re.sub(r'\s+', ' ', get_unicode(text).strip().lower())


class DictionaryES(Dictionary):
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
        logging.getLogger('elasticsearch').setLevel(logging.CRITICAL)

    def _get_index_list_str(self, dics, lang):
        index_list = [self._get_index_name(dic, lang) for dic in dics]
        # filter non-exists indices
        index_list = [idx for idx in index_list if self.es.indices.exists(idx)]
        return ','.join(index_list) if index_list else '%s-*-%s' % (self.prefix_index_name, lang)

    def tag(self, texts, dics, lang):
        result = []
        index_name = self._get_index_list_str(dics, lang)
        for text in texts:
            n_text = self._normalize(text)
            query = {
                'query': {
                    'match': {
                        'voc': n_text
                    }
                }
            }
            hits = scan(client=self.es, query=query, index=index_name, doc_type=self.doc_type)
            tag_voc = {}
            try:
                for hit in hits:
                    doc = hit['_source']
                    voc = doc['voc']
                    pattern = re.compile(r'\b(%s)\b' % voc, re.IGNORECASE)
                    if pattern.search(n_text):
                        dic = hit['_index'].split('-')[1]
                        if dic in tag_voc:
                            tag_voc[dic]['matches'].add(voc)
                            tag_voc[dic]['count'] += 1
                        else:
                            tag_voc[dic] = {'matches': {voc}, 'count': 1}

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

            result.append({
                'norm_text': n_text,
                'tag': tag_voc
            })
        return result

    def get_voc(self, dics, lang):
        result = []
        index_name = self._get_index_list_str(dics, lang)
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
        self.logger.info('Start add_voc...')
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
                            }
                        }
                    }
                },
                'settings': {
                    'index': {
                        'number_of_shards': 1
                    }
                }
            }
            self.es.indices.create(index_name, body=body)

        # normalize vocabularies
        vocs = [self._normalize(v) for v in vocs]

        # check exist vocs
        if not first_init:
            existed_voc = self._get_exist_voc(vocs, index_name, self.doc_type)
            self.logger.debug('existed vocs: %s' % existed_voc)
            vocs = [v for v in vocs if v not in existed_voc]

        if not vocs:
            self.logger.info('All vocabularies has been added')
            return 0, 0

        self.logger.debug('remain vocs: %s' % vocs)

        index_actions = []
        for voc in vocs:
            index_actions.append({
                '_op_type': 'index',
                '_index': index_name,
                '_type': self.doc_type,
                '_id': voc,
                '_source': {
                    'voc': voc
                }
            })
        stats = bulk(self.es, index_actions, stats_only=True, refresh=True)
        self.logger.info('Index Success/Fail: %s/%s' % stats)
        self.logger.info('End add_voc...')
        return stats

    def _get_index_name(self, dic, lang):
        return '%s-%s-%s' % (self.prefix_index_name, dic, lang)

from abc import abstractmethod, ABCMeta
import re
from elasticsearch.helpers import bulk, scan
from util.database import get_es_client
from util.utils import get_logger


class Dictionary(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_voc(self, vocs, dic):
        pass

    @abstractmethod
    def get_voc(self, dics):
        pass

    @abstractmethod
    def tag(self, texts, dics):
        pass

    @staticmethod
    def _normalize(text):
        return re.sub(r'\s+', ' ', text.strip().lower())


class DictionaryES(Dictionary):
    def tag(self, texts, dics):
        result = []
        doc_type = ','.join(dics) if dics else None
        for text in texts:
            n_text = self._normalize(text)
            query = {
                'query': {
                    'match': {
                        'voc': n_text
                    }
                }
            }
            hits = self.es_client.search(self.index_name, doc_type, query)
            tag = []
            for hit in hits['hits']['hits']:
                doc = hit['_source']
                voc = doc['voc']
                pattern = re.compile(r'\b%s\b' % voc, re.IGNORECASE)
                if pattern.search(n_text):
                    dic = hit['_type']
                    tag.append(dic)
                    n_text = pattern.sub('[' + dic + ']', n_text)

            # count tag
            tag_count = {}
            for t in tag:
                if t in tag_count:
                    tag_count[t] += 1
                else:
                    tag_count[t] = 1

            # append empty tag
            for dic in dics:
                if dic not in tag_count:
                    tag_count[dic] = 0

            result.append({
                'norm_text': n_text,
                'tag': tag_count
            })
        return result

    def get_voc(self, dics):
        result = []
        doc_type = ','.join(dics) if dics else None
        dic_vocs = {}
        query = {
            'query': {
                'match_all': {}
            }
        }
        hits = scan(client=self.es_client, index=self.index_name, doc_type=doc_type, query=query)
        for hit in hits:
            dic_name = hit['_type']
            doc = hit['_source']
            if dic_name in dic_vocs:
                dic_vocs[dic_name].append(doc['voc'])
            else:
                dic_vocs[dic_name] = [doc['voc']]

        for dic, vocs in dic_vocs.items():
            result.append({
                'dic': dic,
                'num_voc': len(vocs),
                'vocs': vocs
            })

        return result

    def add_voc(self, vocs, dic):
        self.logger.info('Start add_voc...')
        index_actions = []
        for voc in vocs:
            voc = self._normalize(voc)
            index_actions.append({
                '_op_type': 'index',
                '_index': self.index_name,
                '_type': dic,
                '_id': voc,
                '_source': {
                    'voc': voc
                }
            })
        stats = bulk(self.es_client, index_actions, stats_only=True, refresh=True)
        self.logger.info('Index Success/Fail: %s/%s' % stats)
        self.logger.info('End add_voc...')
        return stats

    def __init__(self):
        self.es_client = get_es_client()
        self.index_name = 'dictionary'
        self.logger = get_logger(self.__class__.__name__)

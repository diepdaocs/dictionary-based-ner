from flask import request
from flask_restplus import Api, Resource

from app import app
from dictionary import DictionaryES
from text_stats import TextStats
from util.utils import get_logger, get_unicode

logger = get_logger(__name__)

api = Api(app, doc='/doc/', version='1.0', title='Named entity tagging')

ns_dic = api.namespace('dictionary', 'Manage dictionaries')

support_languages = ['arabic', 'armenian', 'basque', 'brazilian', 'bulgarian', 'catalan', 'cjk', 'czech',
                     'danish', 'dutch', 'english', 'finnish', 'french', 'galician', 'german', 'greek',
                     'hindi',
                     'hungarian', 'indonesian', 'irish', 'italian', 'latvian', 'lithuanian', 'norwegian',
                     'persian',
                     'portuguese', 'romanian', 'russian', 'sorani', 'spanish', 'swedish', 'turkish',
                     'thai']


@ns_dic.route('/manage')
class DictionaryManageResource(Resource):
    """Manage dictionaries"""
    @api.doc(params={'vocs': 'The vocabularies for adding, if many, separate by comma',
                     'dic': 'The dictionary name for vocabularies',
                     'lang': 'The dictionary language, default is `english`, supported languages are `%s`, '
                             'if language is not supported, use `standard` which support almost european languages'
                     % ', '.join(support_languages)})
    @api.response(200, 'Success')
    def put(self):
        """Add vocabularies to dictionary
        """
        result = {
            'error': False,
            'message': ''
        }
        vocs = request.values.get('vocs', '')
        vocs = [v.strip().lower() for v in vocs.split(',') if v]
        if not vocs:
            result['error'] = True
            result['message'] = 'vocs is empty'
            return result

        dic = request.values.get('dic', '')
        if not dic:
            result['error'] = True
            result['message'] = 'dic is empty'
            return result

        lang = request.values.get('lang', 'english')

        d = DictionaryES()
        success, fail = d.add_voc(vocs, dic, lang)
        result['message'] = "%s vocabularies was added to dictionary '%s' successfully, %s failed" \
                            % (success, dic, fail)
        return result

    @api.doc(params={'dics': 'The dictionaries for getting vocabularies, if many, separate by comma, if empty, get all',
                     'lang': 'The dictionary language, default is `english`'})
    @api.response(200, 'Success')
    def get(self):
        """Get dictionary vocabularies"""
        result = {
            'error': False,
            'message': ''
        }
        dics = request.values.get('dics', '')
        dics = [u.strip().lower() for u in dics.split(',') if u]

        lang = request.values.get('lang', 'english')

        d = DictionaryES()
        result['dics'] = d.get_voc(dics, lang)
        return result

    @api.doc(params={'dics': 'The dictionaries name to be deleted, if many, separate by comma',
                     'lang': 'The dictionary language, default is `english`'})
    @api.response(200, 'Success')
    def delete(self):
        """Delete dictionaries"""
        result = {
            'error': False,
            'message': ''
        }
        dics = request.values.get('dics', '')
        dics = [u.strip().lower() for u in dics.split(',') if u]
        if not dics:
            result['error'] = True
            result['message'] = 'Dictionaries name is empty'
            return result

        lang = request.values.get('lang', 'english')

        d = DictionaryES()
        result['dics'] = d.remove_dic(dics, lang)
        return result


@ns_dic.route('/vocab/delete')
class VocabularyResource(Resource):
    @api.doc(params={'dic': 'The dictionaries name',
                     'vocs': 'The vocabularies to be deleted, if many, separate by comma',
                     'lang': 'The dictionary language, default is `english`'})
    @api.response(200, 'Success')
    def delete(self):
        """Delete dictionary vocabularies"""
        result = {
            'error': False,
            'message': ''
        }
        dic = request.values.get('dic', '')
        if not dic:
            result['error'] = True
            result['message'] = 'dic is empty'
            return result

        vocs = request.values.get('vocs', '')
        vocs = [v.strip().lower() for v in vocs.split(',') if v]
        if not vocs:
            result['error'] = True
            result['message'] = 'vocs is empty'
            return result

        lang = request.values.get('lang', 'english')

        d = DictionaryES()
        success, fail = d.remove_voc(dic, vocs, lang)
        result['message'] = '%s was removed successfully, %s failed' % (success, fail)
        return result

ns_ne = api.namespace('stats', 'Named entity recognition')


@ns_ne.route('/ner')
class NamedEntityTaggingResource(Resource):
    """Named entity tagging"""
    @api.doc(params={'texts': 'The texts for NER, if many, separate by comma',
                     'count_only': 'Specific string for counting in each text',
                     'lookup': 'Dictionaries for tagging, if empty, get all',
                     'lang': 'The dictionary language, default is `english`'})
    @api.response(200, 'Success')
    def post(self):
        """Post texts for named entity recognition"""
        result = {
            'error': False,
            'message': ''
        }
        texts = request.values.get('texts', '')
        texts = [t.strip() for t in texts.split(',') if t]
        if not texts:
            result['error'] = True
            result['message'] = 'texts is empty'
            return result

        count_only = request.values.get('count_only', '')
        lookup = request.values.get('lookup', '')
        lookup = [l.strip().lower() for l in lookup.split(',') if l]

        lang = request.values.get('lang', 'english')

        stats = TextStats()
        logger.info('Process request with texts=%s, count_only=%s, lookup=%s, lang=%s' %
                    ([get_unicode(t) for t in texts], count_only, lookup, lang))
        result['texts'] = stats.get_stats(texts, count_only, lookup, lang)
        return result

from flask import Flask, request
from flask_restplus import Api, Resource, fields

from dictionary import DictionaryES
from text_stats import TextStats
from util.utils import get_logger

logger = get_logger(__name__)

app = Flask(__name__)
api = Api(app, doc='/doc/', version='1.0', title='Named entity tagging')

ns_dic = api.namespace('dictionary', 'Manage dictionaries')


@ns_dic.route('/manage')
class DictionaryManageResource(Resource):
    """Manage dictionaries"""
    @api.doc(params={'vocs': 'The vocabularies for adding, if many, separate by comma',
                     'dic': 'The dictionary name for vocabularies'})
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

        d = DictionaryES()
        success, fail = d.add_voc(vocs, dic)
        result['message'] = "%s vocabularies was added to dictionary '%s' successfully, %s failed" \
                            % (success, dic, fail)
        return result

    @api.doc(params={'dics': 'The dictionaries for getting vocabularies, if many, separate by comma, if empty, get all'})
    @api.response(200, 'Success')
    def get(self):
        """Get dictionary vocabularies"""
        result = {
            'error': False,
            'message': ''
        }
        dics = request.values.get('dics', '')
        dics = [u.strip().lower() for u in dics.split(',') if u]

        d = DictionaryES()
        result['dics'] = d.get_voc(dics)
        return result

ns_ne = api.namespace('stats', 'Named entity recognition')


@ns_ne.route('/ner')
class NamedEntityTaggingResource(Resource):
    """Named entity tagging"""
    @api.doc(params={'texts': 'The texts for NER, if many, separate by comma',
                     'count_only': 'Specific string for counting in each text',
                     'lookup': 'Dictionaries for tagging, if empty, get all'})
    @api.response(200, 'Success')
    def post(self):
        """Post texts for named entity recognition"""
        result = {
            'error': False,
            'message': ''
        }
        texts = request.values.get('texts', '')
        texts = [t.strip().lower() for t in texts.split(',') if t]
        if not texts:
            result['error'] = True
            result['message'] = 'texts is empty'
            return result

        count_only = request.values.get('count_only', '')
        lookup = request.values.get('lookup', '')
        lookup = [l.strip().lower() for l in lookup.split(',') if l]

        stats = TextStats()
        result['texts'] = stats.get_stats(texts, count_only, lookup)
        return result

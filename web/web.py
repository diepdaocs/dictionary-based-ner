import json
import os

from flask import render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd

from app import app
# This is the path to the upload directory
from dictionary import DictionaryES
from text_stats import TextStats
from util.utils import get_logger

app.config['UPLOAD_FOLDER'] = 'web/upload'
# These are the extension that we are accepting to be uploaded
sup_file_type = {'csv'}
app.config['ALLOWED_EXTENSIONS'] = sup_file_type

logger = get_logger(__name__)


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload/dic', methods=['POST'])
def upload_dic():
    dic_name = request.values.get('dic_name')
    if not dic_name or not dic_name.strip():
        return render_template('message.html', message='Dictionary is empty')

    dic_lang = request.values.get('dic_lang')
    if not dic_lang or not dic_lang.strip():
        dic_lang = 'english'

    file_dic = request.files.get('file_dic')
    if file_dic and allowed_file(file_dic.filename):
        file_dic_name = secure_filename(file_dic.filename)
        file_dic_path = os.path.join(app.config['UPLOAD_FOLDER'], file_dic_name)
        file_dic.save(file_dic_path)
        df = pd.read_csv(file_dic_path, encoding='utf-8')
        if 'vocabulary' not in df:
            return render_template('message.html', message="File csv must contain 'vocabulary' field")
        lst_voc = [v for v in df['vocabulary'].tolist() if v and type(v) not in (int, float) and v.strip()]
        os.remove(file_dic_path)
        if not lst_voc:
            return render_template('message.html', message='List vocabularies is empty')
        d = DictionaryES()
        success, fail = d.add_voc(lst_voc, dic_name, dic_lang)
        return render_template('message.html', message='Add %s vocabularies successfully, %s failed' % (success, fail))

    elif not allowed_file(file_dic.filename):
        return render_template('message.html', message='File type is not supported, supported file type is %s'
                                                       % ', '.join(sup_file_type))

    return render_template('message.html', message='Something error')


@app.route('/ne/tag', methods=['POST'])
def tag_ne():
    lookup = request.values.get('lookup', '')
    lookup = [l.strip().lower() for l in lookup.split(',') if l]

    lookup_lang = request.values.get('lookup_lang')
    if not lookup_lang or not lookup_lang.strip():
        lookup_lang = 'english'

    count_only = request.values.get('count_only', '')
    match_type = request.values.get('match_type', 'broad').strip().lower()
    if match_type not in ['broad', 'exact']:
        return render_template('message.html', message='Text matching type `%s` is not supported' % match_type)

    file_text = request.files.get('file_text')
    if file_text and allowed_file(file_text.filename):
        file_text_name = secure_filename(file_text.filename)
        file_text_path = os.path.join(app.config['UPLOAD_FOLDER'], file_text_name)
        file_text.save(file_text_path)
        df = pd.read_csv(file_text_path, encoding='utf-8')
        if 'text' not in df:
            return render_template('message.html', message="File csv must contain 'text' field")

        lst_text = [v for v in df['text'].tolist() if v and v.strip()]
        os.remove(file_text_path)
        if not lst_text:
            return render_template('message.html', message='List text is empty')
        s = TextStats()
        texts_stats = s.get_stats(lst_text, count_only, lookup, lookup_lang, match_type)
        df['type'] = ''
        df['norm_text'] = ''
        df['tag'] = ''
        df['num_word'] = ''
        df['num_count_only'] = ''
        for idx, row in df.iterrows():
            row['type'] = texts_stats[idx]['type']
            row['norm_text'] = texts_stats[idx]['norm_text']
            row['tag'] = json.dumps(texts_stats[idx]['tag'], encoding='utf-8', ensure_ascii=False)
            row['num_word'] = texts_stats[idx]['num_word']
            row['num_char'] = texts_stats[idx]['num_char']
            row['num_count_only'] = texts_stats[idx]['num_count_only']

        df.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'result.csv'), index=False, encoding='utf-8')
        return redirect(url_for('download_file', filename='result.csv'))

    elif not allowed_file(file_text.filename):
        return render_template('message.html', message='File type is not supported, supported file type is %s'
                                                       % ', '.join(sup_file_type))

    return render_template('message.html', message='Something error')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

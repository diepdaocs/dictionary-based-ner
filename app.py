from flask import Flask

app = Flask(__name__, static_folder='web/static', template_folder='web/template')
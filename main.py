from app import app
from web import web
import api

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1999)

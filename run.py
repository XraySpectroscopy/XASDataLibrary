#!/usr/bin/env python
"""
simple script to run XAS Data Library in a test web server
"""

from werkzeug.middleware.profiler import ProfilerMiddleware
from xaslib import app

# Note: Change This Key, used for Flask cookies
# SECRET_KEY = 'xaslib_'+base64.b64encode(os.urandom(32))[:16]
SECRET_KEY = 'xaslib_Rex_QO#C$#JES'

DEBUG = True

PORT = 7112
cnf = app.config
cnf['LOCAL_USE_ONLY'] = False
cnf['ADMIN_EMAIL'] = 'xaslib@xrayabsorption.org'
cnf['BASE_URL'] = 'http://127.0.0.1:%d' % PORT
cnf['DBNAME']  =  'xaslib.db'
cnf['DBCONN']  = dict(user='xasdb', password='secret',
                      host='localhost', server='sqlite3')
cnf['UPLOAD_FOLDER'] = '/tmp/xaslib_uploads'
cnf['DOWNLOAD_FOLDER'] = '/tmp/xaslib_public'
cnf['MAX_CONTENT_LENGTH'] = 33554432

app.jinja_env.cache = {}
app.debug  = True
app.secret_key = SECRET_KEY


# app.config['PROFILE'] = True
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])
app.run(debug=True, port=PORT)

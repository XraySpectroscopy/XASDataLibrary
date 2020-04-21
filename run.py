
from xaslib import app

# Note: Change This Key, used for Flask cookies
# SECRET_KEY = 'xaslib_'+base64.b64encode(os.urandom(32))[:16]
SECRET_KEY = 'xaslib_secret_key_0hrZzetj5rDDSQXv'


PORT = 7112
cnf = app.config
cnf['ADMIN_EMAIL'] = 'xaslib@xrayabsorption.org'
cnf['BASE_URL']    = 'https://data.xrayabsorption.org'
cnf['DBNAME']  =  'xaslib.db'
cnf['DBCONN']  = dict(user='xasdb', password='secret',
                      host='localhost', server='sqlite3')
cnf['UPLOAD_FOLDER'] = '/tmp/xaslib_uploads'
cnf['MAX_CONTENT_LENGTH'] = 33554432

app.jinja_env.cache = {}
app.secret_key = SECRET_KEY

app.run(port=PORT)

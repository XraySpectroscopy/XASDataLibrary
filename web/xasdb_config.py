# used for Flask cookies
SECRET_KEY = 'some long random string goes here'

DBNAME = 'xaslib.db'

DBCONN = dict(user='xasdb',
              password='secret',
              host='localhost',
              server='sqlite3')

PORT = 7112
DEBUG = True
UPLOAD_FOLDER = '/tmp'
ADMIN_EMAIL = 'xaslib@xrayabsorption.org'
BASE_URL    = 'https://data.xrayabsorption.org'
LOCAL_ONLY  = False

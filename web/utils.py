import os
import time
import base64

def make_secret_key():
    "make a secret key for web app"
    f = open('secret.py', 'w')
    f.write("session_key = '%s'\n" % base64.b64encode(os.urandom(36)))
    f.close()

def get_session_key_DISK():
    try:
        from secret import session_key
    except ImportError:
        make_secret_key()
        time.sleep(0.5)
        from secret import session_key
    return session_key

def get_session_key():
    return base64.b64encode(os.urandom(36))

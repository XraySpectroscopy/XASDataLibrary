
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

import xasdb

from utils import get_session_key

# configuration
DATABASE = 'example.db'
PORT     = 7112
DEBUG    = True
SECRET_KEY = get_session_key()

# PTABLE     = make_ptable()

app = Flask(__name__)
app.config.from_object(__name__)

db = xasdb.connect_xasdb(DATABASE)

def session_init():
    if 'username' not in session:
        session['username'] = None
    if 'logged_in' not in session:
        session['logged_in'] = False
    if 'elements' not in session:
        elems = {}
        for e in db.get_elements():
            elems["%i" % e.z]  = (e.symbol, e.name)
        session['elements'] = elems
    if 'edges' not in session:
        edges = {}
        for e in db.get_edges():
            edges["%i"% e.id]  = e.name
        session['edges'] = edges
    if 'spectra' not in session:
        session['spectra'] = []
    if 'spectrum' not in session:
        session['spectrum'] = None

@app.route("/")
def hello():
    session_init()
    return render_template('layout.html')


@app.route('/login/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    session_init()
    error = None
    if session['username'] is not None:
        return redirect(url_for('hello'))
    elif request.method == 'POST':
        if request.form['username'] != 'joe':   # app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != 'who': # app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['username'] = request.form['username']
            return redirect(url_for('ptable'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session_init()
    session.pop('username', None)
    flash('You have been logged out')
    return redirect(url_for('ptable'))

@app.route('/user/')
def user_profile():
    # show the user profile for that user
    session_init()
    if 'username' not in session:
        return 'Not logged in'

    return 'User %s' % session['username']

@app.route('/ptable/')
@app.route('/ptable/<elem>')
def ptable(elem=None):
    session_init()
    # out = ['XAS Data Library']
    # out.append('Username = %s' % session.get('username', 'not logged in'))
    # out.append(PTABLE)
    dbspectra = []
    if elem is not None:
        try:
            dbspectra = db.get_spectra(element=elem)
        except:
            pass
    out = []

    persons = {}
    for p in db.get_persons():
        persons[p.id]  = (p.email, p.name)

    session['nspectra'] = len(dbspectra)
    session['elem'] = elem

    for s in dbspectra:
        edge = session['edges']["%i" % s.edge_id]
        elem_sym, elem_name = session['elements']["%i" % s.element_z]
        person_email, person_name = persons[s.person_id]

        out.append({'id': s.id,
                    'name': s.name,
                    'element': elem,
                    'edge': edge,
                    'person_email': person_email,
                    'person_name': person_name,
                    'elem_sym': elem_sym})

    session['spectra'] = out
    return render_template('ptable.html')

@app.route('/spectrum/<int:id>')
def spectrum(id=None):
    session_init()
    persons = {}
    for p in db.get_persons():
        persons[p.id]  = (p.email, p.name)

    s  = db.get_spectrum(id)
    edge = session['edges']["%i" % s.edge_id]
    elem_sym, elem_name = session['elements']["%i" % s.element_z]
    person_email, person_name = persons[s.person_id]

    session['spectrum'] = {'id': s.id,
                           'name': s.name,
                           'element': elem_name,
                           'edge': edge,
                           'person_email': person_email,
                           'person_name': person_name,
                           'elem_sym': elem_sym}
    return render_template('spectrum.html')

@app.route('/rawfile/<int:id>/<fname>')
def rawfile(id, fname):
    session_init()
    return 'show %i /  %s ' % (id, fname)

@app.route('/showplot/<int:id>/<fname>')
def showplot(id, fname):
    session_init()
    return 'show plot %i /  %s ' % (id, fname)


@app.route('/about')
def about():
    session_init()
    return 'The about page'

if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(port=7112)

from flask import Flask
app = Flask(__name__)

import periodictable
import xasdb
import larch

db = xasdb.connect_xasdb('example.db')
_larch = larch.Interpreter()
app.debug = True


@app.route("/")
def hello():
    return "Hello World!"

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

@app.route('/ptable/')
@app.route('/ptable/<elem>')
def ptable(elem=None):
    ptab = periodictable.make_ptable()
    if elem is not None:
        spectra = db.get_spectra(element=elem)
        out = ['%i spectra for element <b>%s</b>'  % (len(spectra), elem)]
        #for x in dir(_larch.symtable._xafs):
        #    out.append(x)
        for i in spectra:
            out.append("%s, edge=%i, person=%i" % (i.name, i.edge_id, i.person_id))
        ptab = "%s<hr>%s" %  (ptab, "<br>".join(out))

    return ptab

                      
        
@app.route('/about')
def about():
    return 'The about page'

if __name__ == "__main__":
    app.run(port = 7112)

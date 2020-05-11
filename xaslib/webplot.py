import io

import base64

import numpy as np
import matplotlib
matplotlib.use('agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from matplotlib.font_manager import FontProperties
from matplotlib import rcParams

mpl_lfont = FontProperties()
mpl_lfont.set_size(18)
rcParams['xtick.labelsize'] =  rcParams['ytick.labelsize'] = 18

import json
import plotly

from larch.xafs.pre_edge import preedge

PLOTLY_CONFIG = {'displaylogo': False,
                 'modeBarButtonsToRemove': [ 'hoverClosestCartesian',
                                             'hoverCompareCartesian',
                                             'toggleSpikelines']}


def xafs_plotly(x, y, title, ylabel='mutrans', refer=None,
                x_range=None, y_range=None):

    data = [{'x': x.tolist(),
             'y': y.tolist(),
             'type': 'scatter',
             'name': 'data',
             'line': {'width': 3},
             'hoverinfo': 'skip'}]
    if refer is not None:
        data.append({'x': x.tolist(),
                     'y': refer.tolist(),
                     'type': 'scatter',
                     'name': 'reference',
                     'line': {'width': 3},
                     'hoverinfo': 'skip'})

    layout = {'title': title,
              'height': 350,
              'width': 500,
              'showlegend': len(data) > 1,
              'xaxis': {'title': {'text': 'Energy (eV)'},
                        'tickformat': '.0f'},
              'yaxis': {'title': {'text': ylabel},
                        'zeroline': False,
                        'tickformat': '.2f'},
              'modebar': {'orientation': 'h'},
              }
    if x_range is not None:
        layout['xaxis']['range'] = x_range
    if y_range is not None:
        layout['yaxis']['range'] = y_range

    return json.dumps({'data': data, 'layout': layout, 'config': PLOTLY_CONFIG})


def plot_multiple_spectra(db, spectra_list, title=None, max_spectra=20):
    data = []
    xmin, xmax, ymin, ymax = [], [], [], []
    for spid in spectra_list:
        # now get real data for plotting
        energy, mudata, dgroup = None, None, None
        try:
            s  = db.get_spectrum(spid)
            mode = db.get_spectrum_mode(spid)
            if mode.startswith('trans'):
                energy = np.array(json.loads(s.energy))
                i0     = np.array(json.loads(s.i0))
                itrans = np.array(json.loads(s.itrans))
                mudata = -np.log(itrans/i0)
            else:
                energy = np.array(json.loads(s.energy))
                i0     = np.array(json.loads(s.i0))
                ifluor = np.array(json.loads(s.ifluor))
                mudata = ifluor/i0
        except:
            pass
        if energy is not None and mudata is not None:
            dgroup = preedge(energy, mudata)
        if dgroup is not None:
            data.append({'x': energy.tolist(),
                         'y': dgroup['norm'].tolist(),
                         'type': 'scatter',
                         'name': s.name,
                         'line': {'width': 3},
                         'hoverinfo': 'skip'})
            xmin.append(energy.min())
            xmax.append(energy.max())
            ymin.append(dgroup['norm'].min())
            ymax.append(dgroup['norm'].max())
            if len(data) >= max_spectra:
                break


    if len(data) < 0:
        return

    xmin = np.array(xmin).min()
    xmax = np.array(xmax).max()
    ymin = np.array(ymin).min()
    ymax = np.array(ymax).max()
    xmax += (xmax-xmin)*0.05
    xmin -= (xmax-xmin)*0.05
    ymax += (ymax-ymin)*0.05
    ymin -= (ymax-ymin)*0.05

    if title is None:
        title = 'Plot of %d spectra' % (len(data))

    layout = {'title': title,
              'height': 600,
              'width': 1000,
              'showlegend': len(data) > 1,
              'xaxis': {'title': {'text': 'Energy (eV)'},
                        'tickformat': '.0f', 'range': [xmin, xmax]},
              'yaxis': {'title': {'text': 'Normalized XAS'},
                        'zeroline': False,
                        'tickformat': '.2f', 'range': [ymin, ymax]},
              'modebar': {'orientation': 'h'},
              }
    return json.dumps({'data': data, 'layout': layout, 'config': PLOTLY_CONFIG})


def make_xafs_plot(x, y, title, xlabel='Energy (eV)', ylabel='mu', x0=None,
                   ref_mu=None, ref_name=None):

    fig  = Figure(figsize=(8.5, 5.0), dpi=300)
    canvas = FigureCanvas(fig)
    axes = fig.add_axes([0.16, 0.16, 0.75, 0.75])

    axes.set_xlabel(xlabel, fontproperties=mpl_lfont)
    axes.set_ylabel(ylabel, fontproperties=mpl_lfont)
    axes.plot(x, y, linewidth=3.5)
    ymin, ymax = min(y), max(y)
    if x0 is not None:
        axes.axvline(0, ymin=min(y), ymax=max(y),
                     linewidth=2, color='#CCBBDD', zorder=-10)

    if ref_mu is not None:
        axes.plot(x, ref_mu, linewidth=4, zorder=-5, color='#AA4444')
        ymin = min(ymin, min(ref_mu))
        ymax = max(ymax, max(ref_mu))
        title = "%s (%s)" % (title, ref_name)

    xrange = max(x)-min(x)
    yrange = ymax - ymin

    axes.set_xlim((min(x)-xrange*0.05, max(x)+xrange*0.05), emit=True)
    axes.set_ylim((ymin-yrange*0.05, ymax+yrange*0.05), emit=True)
    axes.set_title(title, fontproperties=mpl_lfont)

    figdata = io.BytesIO()
    fig.savefig(figdata, format='png', facecolor='#FDFDFA')
    figdata.seek(0)
    return base64.b64encode(figdata.getvalue())

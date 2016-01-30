import io

import base64

import numpy as np
import matplotlib
matplotlib.use('agg')
from matplotlib.backends.backend_agg import Figure, FigureCanvas

from matplotlib.font_manager import FontProperties
from matplotlib import rcParams

mpl_lfont = FontProperties()
mpl_lfont.set_size(18)
rcParams['xtick.labelsize'] =  rcParams['ytick.labelsize'] = 18

def make_xafs_plot(x, y, title, xlabel='Energy (eV)', ylabel='mu', x0=None,
                   ref_mu=None, ref_name=None):

    fig  = Figure(figsize=(8.5, 5.0), dpi=300)
    canvas = FigureCanvas(fig)
    axes = fig.add_axes([0.16, 0.16, 0.75, 0.75], axisbg='#FFFFFF')

    axes.set_xlabel(xlabel, fontproperties=mpl_lfont)
    axes.set_ylabel(ylabel, fontproperties=mpl_lfont)
    axes.plot(x, y, linewidth=3.5)
    if x0 is not None:
        axes.axvline(0, ymin=min(y), ymax=max(y),
                     linewidth=2, color='#CCBBDD', zorder=-10)

        if ref_mu is not None:
            axes.plot(x, ref_mu, linewidth=4, zorder=-5, color='#AA4444')
            title = "%s (%s)" % (title, ref_name)
        # ymax = (0.7*max(y) + 0.3 * min(y))
        # axes.text(-25.0, ymax, "%.1f eV" % x0, fontproperties=mpl_lfont)

    xrange = max(x)-min(x)
    yrange = max(y)-min(y)

    axes.set_xlim((min(x)-xrange*0.05, max(x)+xrange*0.05), emit=True)
    axes.set_ylim((min(y)-yrange*0.05, max(y)+yrange*0.05), emit=True)
    axes.set_title(title, fontproperties=mpl_lfont)

    figdata = io.BytesIO()
    fig.savefig(figdata, format='png', facecolor='#FDFDFA')
    figdata.seek(0)
    return base64.b64encode(figdata.getvalue())

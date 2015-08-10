import io

import base64

import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams

mpl_lfont = FontProperties()
mpl_lfont.set_size(9)
rcParams['xtick.labelsize'] =  rcParams['ytick.labelsize'] = 9

def make_xafs_plot(x, y, title, xlabel='Energy (eV)', ylabel='mu', x0=None):
    fig  = plt.figure(figsize=(4.5, 2.75), dpi=100)
    axes = fig.add_axes([0.16, 0.16, 0.75, 0.75], axisbg='#FEFEFE')

    axes.set_xlabel(xlabel, fontproperties=mpl_lfont)
    axes.set_ylabel(ylabel, fontproperties=mpl_lfont)
    axes.set_title(title, fontproperties=mpl_lfont)
    axes.plot(x, y, linewidth=2)
    if x0 is not None:
        axes.axvline(0, ymin=min(y), ymax=max(y),
                     linewidth=1, color='#CCBBDD', zorder=-20)
        # ymax = (0.7*max(y) + 0.3 * min(y))
        # axes.text(-25.0, ymax, "%.1f eV" % x0, fontproperties=mpl_lfont)

    axes.set_xlim((min(x), max(x)), emit=True)

    figdata = io.BytesIO()
    plt.savefig(figdata, format='png', facecolor='#F2F2F0')
    figdata.seek(0)
    return base64.b64encode(figdata.getvalue())

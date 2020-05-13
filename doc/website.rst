
Using the X-ray Absorption Data Library
=========================================================

The X-ray Absorption Data Library (**xaslib**) website
`<https://xaslib.xrayabsorption.org>`_ presensts tools to browse and view a
collection of X-ray Absorption Spectroscopy (XAS) data held by `The
International X-ray Absorption Society <https://xrayabsorption.org>`_.  The
main web page will show a periodic table for browsing spectra by absorbing
element:

.. _web_fig1:

.. figure::  _images/main_webpage.png
    :target: _images/main_webpage.png
    :width: 85%
    :align: center

    The X-ray Absorption Data Library website


Clicking on any of the element symbols will show a list of spectra for that
element.  The form on the right hand side allows further refinement of the
displayed spectra, based on which *Edge*, *Beamline*, *Measurement Mode*,
*Rating*, or *Text* found in the information for the spectra.

As an example element with a relatively small number of spectra, clicking
on **V** will show a table with 5 spectra for vanadium:

.. _web_fig2:

.. figure::  _images/main_vanadium.png
    :target: _images/main_vanadium.png
    :width: 85%
    :align: center

    Spectra selections for vanadium

Here, the table shows spectrum name, Edge measured, the Beamline used, and
an optional Rating for each spectrum.

Clicking on the name of any of the spectra will take you to a page
dedicated for that spectrum, as discussed below.  There are also buttons to
the right of the spectra table to "Plot Spectra" and "Save Zip File" for
spectra selected with the check-boxes.  You can use the "Select All" and
"Select None" links to fill in all or none of the checkboxes.  Clicking on
"Select All" and then "Plot Spectra" will bring up a page with an
interactive plot of the 5 selected spectra.  This will look like this:

.. _web_fig3:

.. figure::  _images/plot_vanadium.png
    :target: _images/plot_vanadium.png
    :width: 85%
    :align: center

    Example plot for selected vanadium spectra.

This plot is interactive in a few ways:

    1. hovering your mouse over the plot will bring up a small toolbar
    allowing you zoom in, zoom out, pan, reset the scale, and save an image
    of the plot.

    2. clicking and dragging will zoom in on a portion of the plot.  You
    can double-click to zoom out, or use the toolbar.

    3. clicking on the entries in the legend (for example the label with
    the blue line and **V2O3**) will toggle whether that spectra is shown
    or hidden in the plot.

This allows you to interactively zoom in to better see the differences in
the V XANES:


.. _web_fig4:

.. figure::  _images/xanes_vanadium.png
    :target: _images/xanes_vanadium.png
    :width: 85%
    :align: center

    Zoom in of vandium XANES.


Returning to the main page (using the browser's "back" button will return
to the earlier page of selected spectra), where you can also use the "Save
Zip File" to download a zip file with the data files for the selected
spectra.




.. _Spectra:

The XAS Spectrum
-----------------------------------------


The data in xaslib contains several kinds of information related to XAS
Spectrum, such as Sample, Beamline, Collection Date, and Person.  A
complete list and explanation of these terms is given below.



The main component of the
individual XAS spectrum is the basic type of data presented in X-ray
Absorption Data Library.  Each spectrum represents :math:`\mu(E)`, the
X-ray absorption coefficient, typically measured in transmission mode.
They consist of at least two arrays of numerical data with all arrays
having the same number of data points (typically a few hundred data
points).  These arrays


.. _Beamlines:

Beamlines and Facilities
-----------------------------------------

.. _Samples:

Information about Samples
-----------------------------------------

.. _Citations:

Literature Citations
-----------------------------------------

.. _People:

People
-----------------------------------------


.. _Suites:

Suites: Tagging Related Spectra
-----------------------------------------

A suite is a collection of similar spectra. From an organizational point of
view, suites are simply tags that can be applied to spectra.  Each suite
can contain multiple spectra in the sense that each tag can be applied to
multiple spectra.

In addition, each spectra can be assigned to many suites.  With this simple
mechanism of tags, one can build complex sets of spectra, and be able to
assemble suites of something like *V oxides prepared by Person X and
measured at beamline Y*.

.. _Ratings:

Rating Spectra and Suites
-----------------------------

Any individual spectra or suites of spectra can be rated and reviewed by
any person who has logged in.  Scores can range from 0 to 5 (similar to
many on-line shopping sites), and comments or reviews on the spectrum or
suite can be made.


.. _Uploading:

Uploading Data
--------------------

To upload data, you must be logged in, and the data to load must be a   valid XDI file.

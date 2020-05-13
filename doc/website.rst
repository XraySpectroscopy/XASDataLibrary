
Using the X-ray Absorption Data Library
=========================================================

The X-ray Absorption Data Library website
`<https://xaslib.xrayabsorption.org>`_ (xaslib) presensts tools to browse
and investigate a collection of X-ray Absorption Spectroscopy (XAS) data
held by `The International X-ray Absorption Society
<https://xrayabsorption.org>`_.


The main web page will look like this:

.. _web_fig1:

.. figure::  _images/main_webpage.png
    :target: _images/main_webpage.png
    :width: 65%
    :align: center

    The X-ray Absorption Data Library website

Showing a periodic table for browsing elements for which spectra are
included.  That is, clicking on any of the element symbols will show a list
of spectra for that element.  The form on the right hand side allows
further refinement of the displayed spectra, based on which *Edge*,
*Beamline*, *Measurement Mode*, *Rating*, or *Text* found in the
information for the spectra.


The data in xaslib contains several kinds of information related to XAS
Spectrum, such as Sample, Beamline, Collection Date, and Person.  A
complete list and explanation of these terms is given below.



.. _Spectra:

The XAS Spectrum
-----------------------------------------

The main component of the
individual XAS spectrum is the basic type of data presented in X-ray
Absorption Data Library.  Each spectrum represents :math:`\mu(E)`, the
X-ray absorption coefficient, typically measured in transmission mode.
They consist of at least two arrays of numerical data with all arrays
having the same number of data points (typically a few hundred data
points).  These arrays

.. _Metadta:

Metadata
-----------------------------------------


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

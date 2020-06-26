
.. _Spectra:

=============
 XAS Spectra
=============

The main kind of data in the XAS Data Library (XASLIB) is the *X-ray
absorption spectrum*.  In addition to arrays for the Energy and Absorbance
representing :math:`\mu(E)` each XAS spectrum will have many attributes or
*meta-data* associated with it.  The section will describe the attributes
of a Spectrum, and detail which are required.


Required and Important Attributes of Spectra
============================================

Spectra in the XASLIB have many optional attributes, but a few are
required to convey enough information about a spectrum to anyone interested
in using it.  These include:

    * a `name`
    * an `element` attribute - the atomic number of the absorbing element.
    * an `edge` attribute - the name of the edge
      ('K', 'L3', 'L2', 'L1',  'M4', 'M5', etc).
    * an `energy` array, that must represent the selected energy for each
      point in the spectrum.  This must be in units of 'eV', 'keV', or
      'degrees'.
    * an `energy_units` value that must be one of 'eV', 'keV', or
      'degrees' to describe the units of energy.
    * a `mono_dspacing` value that would the best estimate available for the
      d-spacing of the monochromator used, in units of Angstroms. This is
      required if the `energy_units` is `degrees`.  If you do not know the
      value used, picking a nominal value for the monochromator crystal and
      reflection used is
    * a measuerement `mode` describing how the data was collected. Several
      modes are supported - see :ref:`Table of Measurement Modes
      <mode_table>`, with the most common being `transmission` and
      `fluorescence`.
    * one of `itrans` or `ifluor` array.  Usually, `i0` will also be
      included.  If `i0` is not included, `itrans` or `ifluor` will need to
      hold `mu` itself.
    * a `person_id` for the person who is responsible for the spectrum.



Measurement Modes
=================

XAS data can be collected in several `Measurement Modes
<https://xafs.xrayabsorption.org/acronyms.html#terms-for-measurement-modes>`_.
There are fundamentally 2 main categories: `Transmission` and `Fluorescence` or
`Emisssion` modes.  In `Transmission` mode, :math:`\mu(E)` is evaluated as
`-log(itrans/i0)` where `i0` is the incident intensity and `itrans` is the
intensity that has transmitted through the sample.  It is expected that much of
the data in the library on simple compounds will be measured in this mode.

In `Fluorescence` or `Emission` mode, :math:`\mu(E)` is evaluated as
`(ifluor/i0)` where `i0` is the incident intensity and `ifluor` is the
fluoresced intensity emitted by the sample.

The XASLIB supports a number of modes as listed in the table below.  All of
these except `Transmission` are variations or specific ways to measure in
fluorescence or emission mode.

.. _mode_table:

   Table of Measurement Modes

   ==============================   ===============================================================
       Mode                            Description
   ==============================   ===============================================================
   transmission                      transmission intensity through sample
   fluorescence                      X-ray fluorescence (non-specified)
   fluorescence, total yield         X-ray fluorescence, no energy analysis (ion chamber)
   fluorescence, energy analyzed     X-ray fluorescence with an energy dispersive detector
   herfd                             high-energy resolution fluorescence, with a crystal analyzer
   raman                             non-resonant X-ray inelastic scattering
   xeol                              visible or uv light emission
   electron emission                 emitted electrons from sample
   ==============================   ===============================================================


Spectra Attributes
==================


A complete list of Spectrum attributes is:

.. _spectram_attribute_table:

   Table of Spectrum Attributes. Attributes in **bold** are required.  Those in
   :blue:`blue text` indicate a required field that points either to a list of
   pre-defined strings or another entry in the XASLIB database. Those in
   :red:`red text` indicate a set of options from which one must be selected.

   =======================  ===========================================================
   Attribute                     Description
   =======================  ===========================================================
    **name**                 name of spectrum (possibly original file name)
    **description**          short description of spectrum
    **energy**               array for Energy data, in units given by `energy_units`.
    **d_spacing** [1]_       monochromator *d* spacing in Angstroms.
    :blue:`element`          atomic symbol of absorbing element
    :blue:`edge`             name for absorption edge. (`K`, `L3`, etc)
    :blue:`mode`             name of :ref:`measurement mode <mode_table>`.
    :blue:`energy_units`     units for `energy` array. One of `eV`, `keV`, or `degrees`.
    :blue:`reference_mode`   measurement mode for reference.
    :blue:`sample`           sample used for spectrum (link to Sample table)
    :blue:`beamline`         beamline used for spectrum (link to Beamline table)
    :blue:`citation`         literature citation (link to Citation table)
    :blue:`person`           person uploading/owning the spectrum(link to Person table)
    i0 [2]_                  array for I0 (incident) intensity.
    :red:`itrans` [2]_       array for transmission intensity
    :red:`ifluor` [2]_       array for fluorescence / emission intensity
    irefer                   array for refereence intensity
    energy_stderr            array for standard error of energy
    i0_stderr                array for standard error of i0
    itrans_stderr            array for standard error of itrans
    ifluor_stderr            array for standard error of ifluor
    irefer_stderr            array for standard error of irefer
    energy_resolution        description of energy resolution
    energy_notes             additional notes on energy array
    i0_notes                 additional notes on i0 array
    itrans_notes             additional notes on itrans array
    ifluor_notes             additional notes on ifluor array
    irefer_notes             additional notes on irefer array
    submission_date [3]_     date and time the spectrum was submitted (datestring)
    collection_date [3]_     date and time the spectrum was collected (datestring)
    reference_sample [4]_    name of reference sample (simple string)
    temperature              description of sample temperature for measurement
    extra_data               extra data from other method(s) (described in notes)
    rating_summary           summary string for ratings (internal use)
    filetext                 text of XDI file for spectrum
   =======================  ===========================================================

Notes

.. [1] The monochromator *d* spacing is necessary if *energy_units* is
       `degrees` but is also important to help reproduce and shift spectra
       collected at different times or beamlines.If you do not know the
       exact value used, using the nominal value for the monochromator
       crystal used is acceptable.  If the spectra were measured with an
       energy-dispersive or exotic method that did not use a crystal
       monochromator, please give a value of 1.0 and a detailed explanation
       of the energy calibration in the Notes section.

.. [2] it is expected that `i0` will be provided for most data. If it is
       not available, then `itrans` must hold :math:`\mu(E)` in
       transmission or `ifluor` must :math:`\mu(E)` in fluorescence or
       other emission mode.
 
.. [3] dates for submission and collection date should be formatted as
       ISO861 datestring: `YYYY-MM-DDTHH:MM:SS`, though the `T` can be
       replaces with a blank. For example, '2020-06-21 17:51:22'.

.. [4] note that the reference sample is expected to be an obvious and
       reproducible sample, so simply giving its name (eg, "Ni foil")
       should suffice.
       
       

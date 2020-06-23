
.. _Spectra:

XAS Spectra
===========================

The main kind of data in the XAS Data Library (**xaslib**) is the X-ray
absorption spectrum.  Each spectrum will have many attributes associated
with it.  These will include arrays for the Energy and Absorbance
representing :math:`\mu(E)`, and also several other required attributes.

Required and Important Attributes of Spectra
----------------------------------------------------

Spectra in the **xaslib** have many optional attributes, but a few are
required to convey enough information about a spectrum to anyone interested
in using it.  These include:

    * a `name`
    * an `element` attribute - the atomic number of the absorbing element.
    * an `edge` attribute - the name of the edge ('K', 'L3', 'L2', etc).
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
      Measurement modes are supported (see below), with the most common being
      `transmission` and `fluorescence`.
    * one of `itrans` or `ifluor` array.  Usually, `i0` will also be included.
    * a `person_id` for the person who is responsible for the spectrum.


    

Measurement Modes
-------------------------------

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

The **xaslib** supports a number of modes as listed in the table below.  All of
these except `Transmission` are variations or specific ways to measure in
fluorescence or emission mode.

   =============================   ===============================================================      
       Mode                            Description
   =============================   ===============================================================   
   transmission                     transmission intensity through sample
   fluorescence                     X-ray fluorescence (non-specified)
   fluorescence, total yield        X-ray fluorescence, no energy analysis
   fluorescence, energy analyzed    X-ray fluorescence with an energy dispersive detector
   herfd                            high-energy resolution fluorescence, with a crystal analyzer
   raman                            non-resonant X-ray inelastic scattering
   xeol                             visible or uv light emission
   electron emission                emitted electrons from sample
   =============================   ===============================================================


	 
Spectra Attributes
---------------------------------

A complete list of Spectrum attributes is:


   =================   ===========================================================
    Attribute           Description
   =================   ===========================================================
    name                name of spectrum
    description         spectrum description 
    notes               notes for spectrum
    energy              array for Energy (in eV)
    i0                  array for I0 (incident) intensity
    itrans              array for transmission intensity
    ifluor              array for fluorescence / emission intensity
    irefer              array for refereence intensity
    
    extra_data          JSON-encoded data from other method (described in notes)
    person_id           index of the Person who submitted the sample.
   =================   ===========================================================



                                StrCol('energy_stderr'),
                                StrCol('i0_stderr'),
                                StrCol('itrans_stderr'),
                                StrCol('ifluor_stderr'),
                                StrCol('irefer_stderr'),
				
                                StrCol('energy_notes'),
                                StrCol('energy_resolution'),
                                StrCol('i0_notes'),
                                StrCol('itrans_notes'),
                                StrCol('ifluor_notes'),
                                StrCol('irefer_notes'),
                                StrCol('temperature'),
                                StrCol('filetext'),
                                StrCol('comments'),
                                Column('d_spacing', Float),
                                DateCol('submission_date'),
                                DateCol('collection_date'),
                                StrCol('reference_sample'),
                                StrCol('rating_summary'),
                                PointerCol('energy_units'),
                                PointerCol('person'),
                                PointerCol('edge'),
                                PointerCol('mode'),
                                PointerCol('element', keyid='z'),
                                PointerCol('sample'),
                                PointerCol('beamline'),
                                PointerCol('citation'),
                                PointerCol('reference_mode', 'mode')])

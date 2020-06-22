
.. _Spectra:

XAS Spectra
===========================

The main kind of data in the XAS Data Library (**xaslib**) is the X-ray
absorption spectrum.  Each spectrum will have many attributes associated
with it.  These will include arrays for the Energy and Absorbance
representing :math:`\mu(E)`, and also several other required attributes.

Important Attributes of Spectra
-------------------------------------


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


A Sample will have the following fields:

   =====================   ===========================================================
    Column Name             Description
   =====================   ===========================================================
    name                    name of sample
    formula                 chemical formula
    cas_number              CAS number
    material_source         information on source of material
    preparation             description of sample preparation
    image_data              JSON-encoded image for sample (eg, chemical structure)
    xrd_data                JSON-encoded X-ray diffraction data
    extra_data              JSON-encoded data from other method (described in notes)
    notes                   any notes on sample
    person_id               index of Person in `Person` table
   =====================   ===========================================================

   

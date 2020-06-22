
.. _Samples:

Samples
===========================


Each spectrum will have a sample associated with it.
A sample can be used by more than one spectrum, for example if
temperature-dependent spectra are posted.

A Sample will have the following attributes:

   =================   ===========================================================
    Attribute           Description
   =================   ===========================================================
    name                name of sample
    formula             chemical formula
    cas_number          CAS number
    material_source     information on source of material
    preparation         description of sample preparation
    image_data          JSON-encoded image for sample (eg, chemical structure)
    xrd_data            JSON-encoded X-ray diffraction data
    extra_data          JSON-encoded data from other method (described in notes)
    notes               any notes on sample
    person_id           index of the Person who submitted the sample.
   =================   ===========================================================

   

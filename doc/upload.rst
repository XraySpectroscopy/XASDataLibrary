
Uploading Data to the X-ray Absorption Data Library
-------------------------------------------------------

Adding data to the X-ray Absorption Data Library helps keep this library
vibrant and keeps the library useful for all scientists.  If you have data
that could go into this library, and are able and willing to apply the
`Creative Commons Zero
<https://creativecommons.org/share-your-work/public-domain/cc0/>`_ license
to this data as discussed in :ref:`license`, then please do upload that
data.


Data files for uploading need to be ASCII data files no larger than 16Mb.
The file must contain a **Header Section** at the top of the file followed
by a **Data Table Section**.  Only one scan can be extracted from any one
file.

The **Header Section** contains strings that describe the meta-data for the
data file.  Ideally, these will follow the `XAS Data Interchange
Specification
<https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/spec.md>`_.
See `Example Data Files
<https://github.com/XraySpectroscopy/XASDataLibrary/tree/master/data>`_ for
this library.

The **Data Table Section** contains columns for indvidual arrays.  Columns
should be separated or *delimited* by a combination of spaces, tabs, or
commas. Each line of the file (ending with a Newline and optional Carriage
Return character) corresponds to one row of the Data Table, representing one
energy point for the data.  Up to 32 columns will be accessible.

Required arrays and fields when uploading data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Somewhere in the columns of the Data Table there must be columns for

* An array for *Energy* or *Monochromator Angle*, in units of eV, keV, or
  degrees.

* Arrays that can be used to build :math:`\mu(E)` or mu(Energy).  These
  arrays will be columns in the Data Table that may represent of
  :math:`I_0`, :math:`I_{\rm trans}`, :math:`I_{\rm fluor}`,
  :math:`\mu_{\rm trans}` or :math:`\mu_{\rm fluor}`.  Note that it is OK
  to have emission modes other than fluorescence -- they will be treated in
  the same way as fluorescence data.

When uploading data, names for the columns will be automatically deduced
from the data file.  These names these may not be perfectly aligned with
what you expect the column labels to be. Still, when uploading data, you
will be expected to be able to identify which columns are appropriate for
building :math:`\mu(E)`. During the verification process, you will be able
to view plots of the resulting arrays.


You will also be expected to fill in values for some meta-data including:

    1. Sample Name
    2. Absorbing Element and Edge
    3. Monochromator d-spacing or nominal reflecting cut
    4. Energy units ('eV', 'keV', or 'degrees').
    5. Measurement Mode (transmission, fluorescence, or other emission
       options).
    6. Beamline where data was collected (as a choice of known beamlines).
   

Some of this meta-data may be guessed from the file headers. In additions,
some validity and error checking will be done on these values. Ultimately,
the quality of the data relies on you verifying the correctness of these
fields.

Notes on uploading data
~~~~~~~~~~~~~~~~~~~~~~~~~

1. The data will be sorted so that Energy is strictly increasing.  A
   warning will be given if any of the steps in energy value is less than
   0.001 eV, as this may cause problems for some processing software.

2. Ideally, there will be a separate column of :math:`I_0`, but this is
   not required. 

3. You can include data for a reference channel, either :math:`I_{\rm
   refer}` or :math:`\mu_{\rm refer}`.  The referencee channel can itself 
   be in one of three modes:
	 
   a. `transmission`: :math:`I_{\rm refer}` is downstream of :math:`I_{\rm
      trans}` so that :math:`\mu_{\rm refer} = -\ln(I_{\rm refer}/I_{\rm
      trans})`.  This is probably the most common method used.
   b. `fluorescence, i0`: :math:`I_{\rm refer}` is upstream of the sample,
      and measured using scatter from :math:`I_0` so that
      :math:`\mu_{\rm refer} = I_{\rm refer}/I_0`.
   c. `fluorescence, itrans`: :math:`I_{\rm refer}` is downstream of the sample,
      and measured using scatter from :math:`I_{\rm trans}` so that
      :math:`\mu_{\rm refer} = I_{\rm refer}/I_{\rm trans}`.
   d. `murefer`: :math:`\mu_{\rm refer}` itself.

	    
Finally, because uploading files uses finite computing resources, we
reserve the right to restrict or remove any data for any reason without
notice and to ban users who abuse the ability to upload data.

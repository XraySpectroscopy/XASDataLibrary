

Next Generation XAFS Data Library
---------------------------------

This page is a Work-in-Progress Proposal for how to build a *Next
Generation XAFS Data Library* The main idea is to facilitate the
exchange XAFS specra, particularly on model compounds, such as found
in Model Compound Libraries [#f1]_, [#f2]_, [#f3]_, [#f4]_ We will
create a mechanism to store multiple XAFS spectra in a manner that can
be used within dedicated applications and embedded into existing data
processing software with minimal effort.

Motivation
----------

Storing and Exchanging XAFS Data is an common need for everyone using
XAFS. In particular, retrieving data on *Standards* or *Model Compounds*
is a continuing need for analysis. Additionally, data taken on samples
at different facilities and beamlines need to be compared and analyzed
together. At this point, there is no commonly accepted data format for
XAFS data. There have been a few attempts [#f5]_ 

Most beamline data collection software, and most processing and analysis
software use some variation of *ASCII Column Data Files*, in which data
is written as delimited text in a text file with each row representing a
datum of stepped scan in energy, with a *header* of some sort giving
some idea of the files contents. While such files may be easily read by
humans, they may not be so easily to read by machine, as differences in
file formatting conventions mean that there is no standardized way to
specify header information or the contents of the various columns in the
data files.

Thus, while being *human readable*, ASCII Column Data Files are not
always easily interpreted without first-hand knowledge of how the files
were produced. As an important case in point, the data files in the
`Farrel Lytle XAFS Spectra Database <http://ixs.iit.edu/database/>`__
use a few different formats in which energy is stored as monochromator
steps, with the needed information (steps / degree) to decode these
values put in an unmarked place in the header. In addition, it is rare
to have much "meta-data" about sample or measurements conditions
provided in the data file. When they are included, they are usually as
short, cryptic notes difficult to decipher a few months after the
experiment.

In addition, ASCII Column Data Files offer no standard way to hold
multiple spectra. Yet, sharing and comparing multiple spectra is part of
the need when exchanging data. In order to facilitate the sharing data
between beamlines and the exchange (and recognition) of high-quality
data on standards, it is useful to have Data Libraries or Repositories
which a scientist can use at will and exchange with others. A key point
is that not only should data be well-formatted and vetted for quality,
but should also be easily be viewed as a part of Suite of Spectra.

A Data Library is often envisioned as a single centralized Library (see
http://xafs.org/Databases) which is meant to house *Standard Data* with
some assurance of quality and the expectation that the data is to be
shared with the entire community. In contrast, many researchers keep
their own set of data closely guarded and do not want to share their
data. Another model for a Data Library is a set of spectra being shared
between collaborators, but then possibly allowed to have a wider
distribution (say, after some paper has been published). I am
considering all of these as legitimate use cases, and am more interested
here in creating a format that can be used for all these cases.

Implementation Overview
-----------------------

With the motivation from the previous section, the goals for the format
and library are:

1. Store spectra for exchange, especially for model compounds.  Raw
   data, direct from the beamline will probably need to be converted
   to this format.

1. Store information about the sample, measurement conditions, etc.

1. Store *multiple* spectra, either on the same sample or multiple
   samples, and possibly taken at many facilities.

1. Provide programming libraries and simple standalone applications
   that can read, write, and manage such data libraries.  Programming
   libraries would have to support multiple languages.

There are a few reasonable ways to solve this problem. What follows
below is a methods which makes heavy use of *relational databases* and
SQL. The principle argument here is that relational databases offer a
well-understood, proven way to store data with extensible meta-data. The
use of SQL also makes the programming libraries simpler, as they can
rely on tested SQL syntax to access the underlying data store.

Development Code and Data
~~~~~~~~~~~~~~~~~~~~~~~~~

As the XAS Data Library is being developed, code and examples will be
available at http://github.com/newville/xasdatalib

Why SQLite
~~~~~~~~~~

I propose using `SQLite <http://sqlite.org>`__, a widely used, Free
relational database engine as the primary store for the XAFS Data
Library. A key feature of SQLite is that it needs no external server
or configuration -- the database is contained in a single disk
file. SQLite databases can accessed with a variety of tools [#f8]_,
[#f9]_

Challenges Using SQL Tables for Numerical Array
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SQL-based relational databases may not be the most obvious choice for
storing scientific data composing of arrays of related data. One obvious
limitation is that relational databases don't store array data very
well. Thus storing array data in a portable way within the confines of
an SQL database needs special attention. The approach adopted here is to
JSON, which can encapsulate an array, or other complex data structure
into a string.

Using JSON to store array data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`JSON <http://json.org>`__ -- Javascript Object Notation, provides a
standard, easy-to-use method for encapsulating complex data structures
into strings that can be parsed and used by a large number of
programming languages as the original data. In this respect, the
requirements for the XAS Data Library -- numerical arrays of data -- are
fairly modest. Storing array data in strings is, of course, what ASCII
Column Files have done for years, only not with the benefit of a
standard programming interface to read them. As an example, an array of
data [8000, 8001.0 , 8002.0] would be encoded in json as


.. sourcecode:: json

   '[8000, 8001.0, 8002.0]'


This is considerably easier and lighter weight than using XML to encode
array data.

In addition to encoding numerical arrays, JSON can also encode an
`associative array <http://en.wikipedia.org/wiki/Associative_array>`__
(also known as a *Hash Table*, *Dictionary*, *Record*, or *Key/Value
List*. This can be a very useful construct for storing attribute
information. It might be tempting to use such Associative Arrays for
many pieces of data inside the database, this would prevent those data
from being used in SQL SELECT and other statements: such data would not
be available for making relations. But, as Associative Arrays can so
useful and extensible, several of the tables in the database include a
**attributes** column that is always stored as text. This data will be
expected to hold a JSON-encoded Associative Array that may be useful to
complement the corresponding **notes** column. This data cannot be used
directly in searching the database, but may be useful to particular
applications.

Other Challenges When Using SQLite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While robust, powerful and compliant with SQL standards, SQLite does not
always provide as rich set of Data Types as some SQL relational
databases. In particular for the design here, SQLite does not support
Boolean values or Enum fields. Integer Values are used in place of
Boolean Values. Enum values (which may have been used to encode
Elements, Collection Modes, etc) are implemented as indexes into foreign
tables, and JOINs must be used to relate the data in the tables.

Tables and Database Schema
--------------------------

The principle data held in a XAFS Data Library is XAFS Spectra. In
addition, it is useful to include data on Sample preparation,
measurement conditions, and so on. In addition it is useful to be able
to combine several spectra into a *Suite*, and to identify the people
adding to the library. Thus the XAFS Data Library contains the following
main tables: 

.. table:: Main Tables
   :name:  main-tables

   ===================   ==========================================
    Table Name            Description
   ===================   ==========================================
    spectra               main XAS spectra, pointers to other table
    sample                Samples
    crystal_structure     Crystal structures
    person                People 
    citation              Literature or Other Citations
    format                Data Formats
    suite                 Spectra Suites
    facility              Facilities 
    beamline              Beamlines
    monochromator         Monochromators 
    mode                  Modes of Data Collection
    ligand                Ligands
    element               names of Elements 
    edge                  names of x-ray Edges
    energy_units          units for energies stored for a spectra
   ===================   ==========================================

While some of these tables (spectra, sample) are fairly complex, many of
the tables are really quite simple, holding a few pieces of information.

In addition there are a few `Join
Tables <http://en.wikipedia.org/wiki/Junction_table>`__ to tie together
information and allow *Many-to-One* and *Many-to-Many* relations. These
tables include 

.. table:: Join Tables
   :name:  join-tables

   =================   ==========================================
    Table Name          Description
   =================   ==========================================
    spectra_mode        mode(s) used for a particular spectra
    spectra_ligand      ligand(s) present in a particular spectra
    spectra_suite       spectra contained in a suite 
    spectra_rating      People's comments and scores for Spectra
    suite_rating        People's comments and scores for Suites
   =================   ==========================================

A key feature of this layout is that a *Suite* is very light-weight,
simply comprising lists of spectra. Multiple suites can contain an
individual spectra, and a particular spectra can be contained in
multiple suites without repeated data.

The tables are described in more detail below. While many are
straightforward, a few tables may need further explanation.

Spectra Table
~~~~~~~~~~~~~

This is the principle table for the entire database, and needs extensive
discussion. Several of the thorniest issues have to be dealt with in
this table, making this likely to be the place where most attention and
discussion should probably be focused.


.. sourcecode:: sql

   --
   create table spectra (
		id integer primary key
		name text not null, 
		notes text, 
		attributes text, 
		file_link text, 
		data_energy text, 
		data_i0 text default '[1.0]', 
		data_itrans text default '[1.0]', 
		data_iemit text default '[1.0]', 
		data_irefer text default '[1.0]', 
		data_dtime_corr text default '[1.0]', 
		calc_mu_trans text default '-log(itrans/i0)', 
		calc_mu_emit text default '(iemit*dtime_corr/i0)', 
		calc_mu_refer text default '-log(irefer/itrans)', 
		notes_i0 text, 
		notes_itrans text, 
		notes_iemit text, 
		notes_irefer text, 
		temperature text, 
		submission_date datetime, 
		collection_date datetime, 
		reference_used integer, 
		energy_units_id   -- > energy_units table
		monochromator_id  -- > monochromator table
		person_id         -- > person table
		edge_id           -- > edge table
		element_z         -- > element table
		sample_id         -- > sample table
		beamline_id       -- > beamline table
		format_id         -- > format table
		citation_id       -- > citatione table
		reference_id      -- > sample table (for sample used as reference)


We'll discuss the table entries more by grouping several of them
together. First, Each entry in the spectra table contains links to many
other tables.

.. table:: Spectra Table
   :name:  spectra-table

   =====================   ========================================================
    spectra Column Name     Description
   =====================   ========================================================
    energy_units_id         index of energy_units table
    person_id               index of person table for person donating spectra
    edge_id                 index of edge table for X-ray Edge
    element_z               index of element table for absorbing element
    sample_id               index of sample table, describing the sample
    reference_id            index of sample table, describing the reference sample
    beamline_id             index of the beamline where data was collected
    monochromator_id        index of the monochromator table for mono used
    format_id               index of the format table for data format used
    citation_id             index of the citation table for literature citation
   =====================   ========================================================

Next, the table contains ancillary information (you may ask why some of
these are explicit while others are allowed to be put in the
**attributes** field).

.. table:: Ancillary Information Table
   :name:  ancillary-table

   =====================   ===========================================================
    spectra Column Name     Description
   =====================   ===========================================================
    notes                   any notes on data
    attributes              JSON-encoded hash table of extra attributes
    temperature             Sample temperature during measurement
    submission_date         date of submission 
    reference_used          Boolean (0=False, 1=True) of whether a Reference was used
    file_link               link to external file
   =====================   ===========================================================

Here, **reference_used** means whether data was also measured in the
reference channel for additional energy calibration . If 1 (True), the
reference sample must be given. The **file_link** entry would be the
file and path name for an external file. This must be relative to the
directory containing database file itself, and cannot be an absolute
path. It may be possible to include URLs, ....

Finally, we have the information for internally stored data arrays
themselves

.. table:: Stored Data Arrays Table
   :name:  data-table

   =====================   ============================================================   ======================================
    spectra Column Name     Description                                                    Default 
   =====================   ============================================================   ======================================
    data_energy             JSON data for energy                                           --
    data_i0                 JSON data for I_0 (Monitor)                                    1.0 
    data_itrans             JSON data for I_transmission (I_1)                             1.0 
    data_iemit              JSON data for I_emisssion (fluorescence, electron yield)       1.0
    data_irefer             JSON data for I_trans for reference channel                    1.0 
    data_dtime_corr         JSON data for Multiplicative Deadtime Correction for I_emit    1.0
    calc_mu_trans           calculation for mu_transmission                                -log(dat_itrans/dat_i0)
    calc_mu_emit            calculation for mu_emission                                    dat_iemit * dat_dtime_corr / dat_i0
    calc_mu_refer           calculation for mu_reference                                   -log(dat_irefer/dat_itrans)
    calc_energy_ev          calculation to convert energy to eV                            None
    notes_energy            notes on energy 
    notes_i0                notes on dat_i0
    notes_itrans            notes on dat_itrans 
    notes_iemit             notes on dat_iemit 
    notes_irefer            notes on dat_irefer
   =====================   ============================================================   ======================================

The **data_****\*** entries will be JSON encoded strings of the array
data. The calculations will be covered in more detail below. Note that
the **spectra_mode** table below will be used to determine in which
modes the data is recorded.

Data Storage
^^^^^^^^^^^^

As alluded to above, the **data_****\*** will be stored as JSON-encoded
strings.

Encoding Calculations, particularly for "Energy to eV"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The calculations of mu in the various modes are generally well defined,
but it is possible to override them.

Energy Units
^^^^^^^^^^^^

The calculations of mu in the various modes are generally well defined,
but it is possible to override them.

Sample Table
~~~~~~~~~~~~

.. sourcecode:: sql

   -- sample information
   create table sample (
      id               integer primary key, 
      person_id         integer not null,    -- > person table
      crystal_structure_id  integer,        -- > crystal_structure table
      name             text,
      formula          text,
      material_source  text,  
      notes            text,
      attributes       text);



Crystal_Structure Table
~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: sql

   -- crystal information (example format = CIFS , PDB, atoms.inp)
   create table crystal (
      id          integer primary key , 
      format      text not null,
      data        text not null,
      notes       text,
      attributes  text);

Ligand Table
~~~~~~~~~~~~


.. sourcecode:: sql

   create table ligand (
      id integer primary key, 
      name text,
      notes text);

   create table spectra_ligand (
      id       integer primary key, 
      ligand   integer not null,     --> ligand table
      spectra  integer not null);    --> spectra table


Person Table
~~~~~~~~~~~~


.. sourcecode:: sql

   create table person (
      id           integer primary key , 
      email        text not null unique,
      first_name   text not null,
      last_name    text not null,
      sha_password text not null);

Citation Table
~~~~~~~~~~~~~~

.. sourcecode:: sql

   create table citation (
      id           integer primary key , 
      journal      text,
      authors      text,
      title        text,
      volume       text,
      pages        text,
      year         text,
      notes        text,
      attributes   text,  
      doi          text);


Format Table
~~~~~~~~~~~~

.. sourcecode:: sql

   -- spectra format: table of data formats
   --
   --  name='internal-json' means data is stored as json data in spectra table
   -- 
   create table format (
      id          integer primary key, 
      name        text, 
      notes       text,
      attributes  text);

   insert into format (name, notes) values ('internal-json', 'Read dat_*** columns of spectra table as json');


Suite Table
~~~~~~~~~~~

.. sourcecode:: sql

   --  Suite:  collection of spectra
   create table suite (
      id          integer primary key , 
      person      integer not null,     -- > person table
      name        text not null,
      notes       text,
      attributes  text);

   -- SUITE_SPECTRA: Join table for suite and spectra
   create table spectra_suite (
      id       integer primary key , 
      suite    integer  not null,     -- > suite table
      spectra  integer  not null);    -- > spectra table


Rating Table
~~~~~~~~~~~~



A rating is a numerical score given to a Spectra or a Suite of Spectra
by a particular person. Each score can also be accompanied by a comment.

While not enforced within the database itself, the scoring convention
should be *Amazon Scoring*: a scale of 1 to 5, with 5 being best.

.. sourcecode:: sql

   create table rating (
      id         integer primary key , 
      person     integer  not null,    -- > person table
      spectra    integer,              -- > spectra table
      suite      integer,              -- > suite table
      score      integer,
      comments   text);




Monochromator and Collection_Mode Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These two tables simply list standard monochromator types and data
collection modes.

.. sourcecode:: sql

   -- Monochromator descriptions
   create table monochomator (
      id integer primary key, 
      name             text, 
      lattice_constant text, 
      steps_per_degree text, 
      notes            text,
      attributes       text);

   -- XAS collection modes ('transmission', 'fluorescence', ...)
   create table collection_mode (
      id  integer primary key, 
      name text, 
      notes text);
   insert into  collection_mode (name, notes) values ('transmission', 'transmission intensity through sample');
   insert into  collection_mode (name, notes) values ('fluorescence, total yield', 'total x-ray fluorescence intensity, as measured with ion chamber');
   insert into  collection_mode (name, notes) values ('fluorescence, energy analyzed', 'x-ray fluorescence measured with an energy dispersive (solid-state) detector.  These measurements will often need to be corrected for dead-time effects');
   insert into  collection_mode (name, notes) values ('electron emission', 'emitted electrons from sample');
   insert into  collection_mode (name, notes) values ('xeol', 'visible or uv light emission');

   create table spectra_modes (
      id       integer primary key , 
      mode     integer  not null,   -- > collection_mode 
      spectra  integer  not null);  -- > spectra table


Beamline and Facility Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These two tables list X-ray (synchrotron) facilities and particular
beamlines.

Note that a monochromator is optional for a beamline.

.. sourcecode:: sql

   -- beamline description 
   --    must have a facility
   --    a single, physical beamline can be represented many times for different configurations
   create table beamline (
      id            integer primary key ,  
      facility      integer  not null,    --> facility table
      name          text, 
      xray_source   text, 
      monochromator integer,   -- > monochromator table (optional)
      notes         text,
      attributes    text);

   -- facilities
   create table facility (
      id integer primary key, 
      name         text not null unique, 
      notes        text,
      attributes   text);


Element and Edge Tables
~~~~~~~~~~~~~~~~~~~~~~~

These two tables simply list standard symbols and names of the elements
of the periodic table, and the standard names for the x-ray absorption
edges. The schema are

.. sourcecode:: sql

   create table element (z integer primary key, 
                         symbol text not null unique, 
                         name text);
   insert into  element (z, symbol, name) values (1, 'H', 'hydrogen');
   insert into  element (z, symbol, name) values (2, 'He', 'helium');
 

   create table edge (id integer primary key, 
                      name text not null unique, 
                      level text);
   insert into  edge (name,  level) values ('K', '1s');
   insert into  edge (name,  level) values ('L3', '2p3/2');
   insert into  edge (name,  level) values ('L2', '2p1/2');
   insert into  edge (name,  level) values ('L1', '2s');




Supported Low-Level Data Formats
--------------------------------

Initially, the principle data format for the XAS Data library will be
**Internally Stored, JSON-encoded** data arrays. Storing data internally
has the advantage of preserving the database as a single file.
JSON-encoded arrays have the advantage of being readily useful to many
languages and environments. Alternate internal formats could be allowed,
but no such formats are yet identified.

External data

Example Queries
---------------

Programming Interface(s)
------------------------

References, External Links
--------------------------


Notes
-----

.. rubric:: Footnotes

.. [#f1] http://cars9.uchicago.edu/~newville/ModelLib/search.html
.. [#f2] http://ixs.iit.edu/database/
.. [#f3] http://x18b.nsls.bnl.gov/data.htm
.. [#f4] http://ssrl.slac.stanford.edu/mes/spectra/index.html
.. [#f5] `Proposed Format for a single data set from Bruce Ravel and Ken McIvor <http://xafs.org/XasDataFormat>`__
.. [#f6] `Talks from January, 2010 Workshop on HDF5 for Synchrotron Data <http://ftp.esrf.eu/pub/scisoft/HDF5FILES/HDF5_Workshop_2010Jan/>`__
.. [#f7] `Upcoming Workshop (April 2011) on Improving Data for XAFS <http://pfwww.kek.jp/Q2XAFS2011/>`__
.. [#f8] http://sourceforge.net/projects/sqlitebrowser/files/sqlitebrowser/2.0%20beta1/
.. [#f9] https://addons.mozilla.org/en-US/firefox/addon/sqlite-manager/

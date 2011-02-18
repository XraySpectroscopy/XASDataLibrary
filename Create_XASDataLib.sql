
--
create table spectra (
  id               integer primary key, 
  person           integer not null,    -- > person table
  edge             integer not null,    -- > edge table
  element          integer not null,    -- > element table
  sample           integer not null,    -- > sample table
  beamline         integer not null,    -- > beamline table
  monochromator    integer not null,    -- > monochromator table
  format           integer not null,    -- > format table
  citation         integer,             -- > citation table
  temperature      text,  
  notes            text,  
  attributes       text,  
  submission_date  text,
  reference_used   integer,
  npts             integer not null,
  file_link        text,
  dat_energy       text,
  dat_i0           text,
  dat_itrans       text,
  dat_iemit        text,
  dat_irefer       text,
  dat_dtime_corr   text,
  calc_mu_trans    text,
  calc_mu_emit     text,
  calc_mu_refer    text,
  calc_energy_ev   text,
  notes_energy     text,
  notes_i0         text,
  notes_itrans     text,
  notes_iemit      text,
  notes_irefer     text);

-- sample information
create table sample (
  id               integer primary key, 
  person           integer not null,    -- > person table
  crystal          integer,             -- > crystal table
  name             text,
  formula          text,
  material_source  text,  
  notes            text,
  attributes       text);

-- crystal information (example format = CIFS , PDB, atoms.inp)
create table crystal (
  id       integer primary key , 
  format   text not null,
  data     text not null,
  notes       text,
  attributes  text);

-- Persons: 
--   EMAIL           email of person        
--   FIRST_NAME      first name of person   
--   LAST_NAME       last name of person    
--   SHA_PASSWORD    sha1 sum of password   

create table person (
  id           integer primary key , 
  email        text not null unique,
  first_name   text not null,
  last_name    text not null,
  sha_password text not null);

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

-- Ratings:  for spectra or suite
create table rating (
  id         integer primary key , 
  person     integer  not null,    -- > person table
  spectra    integer,              -- > spectra table
  suite      integer,              -- > suite table
  score      integer,
  comments   text);

--  Suite:  collection of spectra
create table suite (
  id        integer primary key , 
  person    integer not null,     -- > person table
  name      text not null,
  notes     text,
  attributes text);

-- SUITE_SPECTRA: Join table for suite and spectra
create table spectra_suite (
  id       integer primary key , 
  suite    integer  not null,     -- > suite table
  spectra  integer  not null);    -- > spectra table


-- facilities
create table facility (
  id integer primary key, 
  name text not null unique, 
  notes         text,
  attributes    text);

-- beamline description 
--    must have a facility
--    a single, physical beamline can be represented many times for different configurations
create table beamline (
  id            integer primary key ,  
  facility      integer  not null,    --> facility table
  name          text, 
  xray_source   text, 
  monochromator integer,  -- > monochromator table (optional)
  notes         text,
  attributes    text);

-- Monochromator descriptions
create table monochomator (
   id integer primary key, 
   name text, 
   lattice_constant text, 
   steps_per_degree text, 
   notes text,
   attributes text);

-- XAS collection modes ('transmission', 'fluorescence', ...)
create table collection_mode (id  integer primary key, name text, notes text);
insert into  collection_mode (name, notes) values ('transmission', 'transmission intensity through sample');
insert into  collection_mode (name, notes) values ('fluorescence, total yield', 'total x-ray fluorescence intensity, as measured with ion chamber');
insert into  collection_mode (name, notes) values ('fluorescence, energy analyzed', 'x-ray fluorescence measured with an energy dispersive (solid-state) detector.  These measurements will often need to be corrected for dead-time effects');
insert into  collection_mode (name, notes) values ('electron emission', 'emitted electrons from sample');
insert into  collection_mode (name, notes) values ('xeol', 'visible or uv light emission');
-- 
create table spectra_modes (
  id       integer primary key , 
  mode     integer  not null,   -- > collection_mode 
  spectra  integer  not null);  -- > spectra table

create table ligand (id integer primary key, name text, notes text);

create table spectra_ligand (
  id       integer primary key, 
  ligand   integer not null,     --> ligand table
  spectra  integer not null);    --> spectra table


-- spectra format: table of data formats
--
--  name='internal-json' means data is stored as json data in spectra table
-- 
create table format (
   id integer primary key, 
   name text, 
   notes text,
   attributes text);

insert into  format (name, notes) values ('internal-json', 'Read dat_*** columns of spectra table as json');

-- elements of the periodic table
create table element (z integer primary key, symbol text not null unique, name text);
insert into  element (z, symbol, name) values (1, 'H', 'hydrogen');
insert into  element (z, symbol, name) values (2, 'He', 'helium');

create table edge (id integer primary key, name text not null unique,  level text);
insert into  edge (name,  level) values ('K', '1s');
insert into  edge (name,  level) values ('L3', '2p3/2');
insert into  edge (name,  level) values ('L2', '2p1/2');
insert into  edge (name,  level) values ('L1', '2s');



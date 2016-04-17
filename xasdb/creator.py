#!/usr/bin/env python
"""
   provides make_newdb() function to create an empty XAS Data Library
"""
import sys
import os
import time
import shutil
from datetime import datetime

from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy import MetaData, create_engine, \
     Table, Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.pool import SingletonThreadPool

def PointerCol(name, other=None, keyid='id', **kws):
    "pointer column"
    if other is None:
        other = name
    return Column("%s_%s" % (name, keyid), None,
                  ForeignKey('%s.%s' % (other, keyid), **kws))

def StrCol(name, size=None, **kws):
    "string column"
    if size is None:
        return Column(name, Text, **kws)
    else:
        return Column(name, String(size), **kws)

def IntCol(name, **kws):
    "integer column"
    return Column(name, Integer, **kws)

def DateCol(name, timezone=True, **kws):
    "datetime column"
    return Column(name, DateTime(timezone=timezone), **kws)

def NamedTable(tablename, metadata, keyid='id', nameid='name',
               name=True, notes=True, cols=None, name_unique=True):
    """create table with name, id, and optional notes colums"""
    args  = [IntCol(keyid, primary_key=True)]
    if name:
        args.append(StrCol(nameid, nullable=False, unique=name_unique))
    if notes:
        args.append(StrCol('notes'))
    if cols is not None:
        args.extend(cols)
    return Table(tablename, metadata, *args)

class InitialData:
    info    = [["version", "1.1.0"],
               ["create_date", '<now>'],
               ["modify_date", '<now>']]

    e_units = [["eV", "electronVolts"],
               ["keV", "kiloelectronVolts"],
               ["degrees","angle in degrees for Bragg monochromator.  Needs mono d_spacing"] ]

    modes = [["transmission", "transmission intensity through sample"],
             ["fluorescence", "X-ray fluorescence, no further details"],
             ["fluorescence, total yield", "X-ray fluorescence, no energy analysis"],
             ["fluorescence, energy analyzed",
              "X-ray fluorescence with an energy dispersive detector"],
             ["xeol", "visible or uv light emission"],
             ["electron emission", "emitted electrons from sample"]]

    facilities = [['SSRL', 'US', 'Palo Alto', 'CA', 'Stanford Synchrotron Radiation Laboratory', 'SLAC'],
                  ['SRS',  'UK',  'Cheshire', '',    'Synchrotron Radiation Source', 'Daresbury Laboratory'],
                  ['NSLS', 'US', 'Upton', 'NY',     'National Synchrotron Light Source', 'BNL'],
                  ['PF',   'Japan', 'Tsukuba', '', 'Photon Factory', 'KEK'],
                  ['ESRF', 'France', 'Grenoble', '', 'European Synchrotron Radiation Facility', ''],
                  ['APS',  'US', 'Argonne', 'IL', 'Advanced Photon Source', 'ANL'],
                  ['ALS',  'US', 'Berkeley', 'CA', 'Advanced Light Source', 'LBNL'],
                  ['DLS',  'UK', 'Didcot', '', 'Diamond Light Source', ''],
                  ['SOLEIL', 'France',  'GIF-sur-YVETTE', '',  'Synchrotron SOLEIL', '' ],
                  ]

    beamlines = [['13ID',  'GSECARS 13-ID',   'APS Undulator A',     6],
                 ['13BM',  'GSECARS 13-BM',   'APS bending magnet',  6],
                 ['10ID',  'MR-CAT  10-ID',   'APS Undulator A',     6],
                 ['10BM',  'MR-CAT  10-BM',   'APS Bending Magnet',  6],
                 ['20ID',  'PNC/XOR 20-ID',   'APS Undulator A',     6],
                 ['20BM',  'PNC/XOR 20-BM',   'APS Bending Magnet',  6],
                 ['X11A',  'NSLS X11-A',      'NSLS bending magnet', 3],
                 ['2-3',   'SSRL, 2-3',       '',                    1],
                 ['4-3',   'SSRL, 4-3',       '',                    1],
                 ['4-1',   'SSRL, 4-1',       '',                    1]]

    edges = [["K", "1s"], ["L3", "2p3/2"],
             ["L2", "2p1/2"], ["L1", "2s"], ["M4,5", "3d3/2,5/2"]]

    elements = [[1, "H", "hydrogen"],  [2, "He", "helium"],
                [3, "Li","lithium"],   [4, "Be", "beryllium"],
                [5, "B", "boron"],     [6, "C", "carbon"],
                [7, "N", "nitrogen"],  [8, "O", "oxygen"],
                [9, "F", "fluorine"],  [10, "Ne", "neon"],
                [11, "Na", "sodium"],  [12, "Mg", "magnesium"],
                [13, "Al", "aluminum"],  [14, "Si", "silicon"],
                [15, "P", "phosphorus"], [16, "S", "sulfur"],
                [17, "Cl", "chlorine"],  [18, "Ar", "argon"],
                [19, "K", "potassium"],  [20, "Ca", "calcium"],
                [21, "Sc", "scandium"],  [22, "Ti","titanium"],
                [23, "V", "vanadium"],   [24, "Cr", "chromium"],
                [25, "Mn","manganese"],  [26, "Fe", "iron"],
                [27, "Co", "cobalt"],    [28, "Ni","nickel"],
                [29, "Cu", "copper"],    [30, "Zn", "zinc"],
                [31, "Ga", "gallium"],   [32, "Ge", "germanium"],
                [33, "As", "arsenic"],   [34, "Se", "selenium"],
                [35, "Br", "bromine"],   [36, "Kr", "krypton"],
                [37, "Rb", "rubidium"],  [38,"Sr", "strontium"],
                [39, "Y", "yttrium"],    [40, "Zr", "zirconium"],
                [41, "Nb", "niobium"],   [42, "Mo", "molybdenum"],
                [43, "Tc", "technetium"], [44, "Ru", "ruthenium"],
                [45, "Rh", "rhodium"],    [46, "Pd", "palladium"],
                [47, "Ag", "silver"],     [48, "Cd", "cadmium"],
                [49, "In", "indium"],     [50, "Sn", "tin"],
                [51, "Sb", "antimony"],   [52, "Te", "tellurium"],
                [53, "I", "iodine"],      [54, "Xe", "xenon"],
                [55, "Cs", "cesium"],     [56, "Ba", "barium"],
                [57, "La", "lanthanum"],  [58, "Ce", "cerium"],
                [59, "Pr", "praseodymium"], [60, "Nd", "neodymium"],
                [61, "Pm", "promethium"],   [62, "Sm", "samarium"],
                [63, "Eu", "europium"],     [64, "Gd", "gadolinium"],
                [65, "Tb", "terbium"],      [66, "Dy", "dysprosium"],
                [67, "Ho", "holmium"],      [68, "Er", "erbium"],
                [69, "Tm", "thulium"],      [70, "Yb", "ytterbium"],
                [71, "Lu", "lutetium"],     [72,"Hf", "hafnium"],
                [73, "Ta", "tantalum"],     [74, "W", "tungsten"],
                [75, "Re","rhenium"],       [76, "Os", "osmium"],
                [77, "Ir", "iridium"],      [78, "Pt", "platinum"],
                [79, "Au", "gold"],         [80, "Hg", "mercury"],
                [81, "Tl", "thallium"],     [82, "Pb", "lead"],
                [83, "Bi", "bismuth"],      [84, "Po","polonium"],
                [85, "At", "astatine"],     [86, "Rn", "radon"],
                [87, "Fr","francium"],      [88, "Ra", "radium"],
                [89, "Ac", "actinium"],     [90, "Th","thorium"],
                [91, "Pa", "protactinium"], [92, "U", "uranium"],
                [93, "Np","neptunium"],     [94, "Pu", "plutonium"],
                [95, "Am", "americium"],    [96, "Cm", "curium"],
                [97, "Bk", "berkelium"],    [98, "Cf", "californium"],
                [99, "Es", "einsteinium"],  [100, "Fm", "fermium"],
                [101, "Md", "mendelevium"], [102, "No", "nobelium"],
                [103, "Lw", "lawerencium"], [104, "Rf", "rutherfordium"],
                [105, 'Ha', "dubnium"],     [106, "Sg", "seaborgium"],
                [107, "Bh", "bohrium"],     [108, "Hs", "hassium"],
                [109, "Mt", "meitnerium"],  [110, "Ds", "darmstadtium"],
                [111, "Rg", "roentgenium"], [112, "Cn", "copernicium"] ]

def  make_newdb(dbname, server= 'sqlite', user='',
                password='',  host='', port=None):
    """create initial xafs data library.  server can be
    'sqlite' or 'postgresql'
    """
    if server.startswith('sqlit'):
        engine = create_engine('sqlite:///%s' % (dbname),
                               poolclass=SingletonThreadPool)
    else: # postgres
        conn_str= 'postgresql://%s:%s@%s:%i/%s'
        if port is None:
            port = 5432

        dbname = dbname.lower()
        # first we check if dbname exists....
        query = "select datname from pg_database"
        pg_engine = create_engine(conn_str % (user, password,
                                       host, port, 'postgres'))
        conn = pg_engine.connect()
        conn.execution_options(autocommit=True)
        conn.execute("commit")
        dbs = [i[0].lower() for i in conn.execute(query).fetchall()]
        if  dbname not in dbs:
            try:
                conn.execute("create database %s" % dbname)
                conn.execute("commit")
            except:
                pass
        conn.close()
        time.sleep(0.5)

        engine = create_engine(conn_str % (user, password, host, port, dbname))

    metadata =  MetaData(engine)


    info = Table('info', metadata,
                 StrCol('key', primary_key=True, unique=True),
                 StrCol('value'))

    ligand  = NamedTable('ligand', metadata)
    mode    = NamedTable('mode', metadata)

    facility = NamedTable('facility', metadata,
                          cols=[StrCol('fullname'),
                                StrCol('laboratory'),
                                StrCol('city'),
                                StrCol('region'),
                                StrCol('country', nullable=False)])

    element = NamedTable('element', metadata, keyid='z', notes=False,
                         cols=[StrCol('symbol', size=2,
                                      unique=True,
                                      nullable=False)])

    edge = NamedTable('edge', metadata, notes=False,
                      cols=[StrCol('level', size=32,
                                   unique=True, nullable=False)])

    energy_units = NamedTable('energy_units', metadata, nameid='units')

    crystal_structure = NamedTable('crystal_structure', metadata,
                                   cols=[StrCol('format'),
                                         StrCol('data')])

    person = NamedTable('person', metadata, nameid='email',
                        cols=[StrCol('name', nullable=False),
                              StrCol('password'),
                              StrCol('affiliation'),
                              StrCol('confirmed')])

    citation = NamedTable('citation', metadata,
                          cols=[StrCol('journal'),
                                StrCol('authors'),
                                StrCol('title'),
                                StrCol('volume'),
                                StrCol('pages'),
                                StrCol('year'),
                                StrCol('doi')])

    sample = NamedTable('sample', metadata, name_unique=False,
                        cols=[StrCol('formula'),
                              StrCol('material_source'),
                              StrCol('preparation'),
                              PointerCol('person'),
                              PointerCol('crystal_structure')
                              ])

    spectrum = NamedTable('spectrum', metadata, name_unique=False,
                          cols=[StrCol('energy'),
                                StrCol('i0'),
                                StrCol('itrans'),
                                StrCol('ifluor'),
                                StrCol('irefer'),
                                StrCol('energy_stderr'),
                                StrCol('i0_stderr'),
                                StrCol('itrans_stderr'),
                                StrCol('ifluor_stderr'),
                                StrCol('irefer_stderr'),
                                StrCol('energy_notes'),
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
                                IntCol('reference_used'),
                                PointerCol('energy_units'),
                                PointerCol('person'),
                                PointerCol('edge'),
                                PointerCol('element', keyid='z'),
                                PointerCol('sample'),
                                PointerCol('beamline'),
                                PointerCol('citation'),
                                PointerCol('reference_mode', 'mode'),
                                PointerCol('reference', 'sample'),
                                StrCol('rating_summary')])

    suite = NamedTable('suite', metadata,
                       cols=[PointerCol('person'),
                             StrCol('rating_summary'),
                             ])

    beamline = NamedTable('beamline', metadata,
                          cols=[StrCol('xray_source'),
                                PointerCol('facility')] )

    spectrum_rating = Table('spectrum_rating', metadata,
                            IntCol('id',  primary_key=True),
                            IntCol('score'),
                            DateCol('datetime'),
                            StrCol('comments'),
                            PointerCol('person') ,
                            PointerCol('spectrum'))

    suite_rating = Table('suite_rating', metadata,
                         IntCol('id',  primary_key=True),
                         IntCol('score'),
                         DateCol('datetime'),
                         StrCol('comments'),
                         PointerCol('person') ,
                         PointerCol('suite'))

    spectrum_suite = Table('spectrum_suite', metadata,
                           IntCol('id', primary_key=True),
                           PointerCol('suite') ,
                           PointerCol('spectrum'))

    spectrum_mode = Table('spectrum_mode', metadata,
                          IntCol('id', primary_key=True),
                          PointerCol('mode') ,
                          PointerCol('spectrum'))

    spectrum_ligand = Table('spectrum_ligand', metadata,
                           IntCol('id', primary_key=True),
                           PointerCol('ligand'),
                           PointerCol('spectrum'))

    metadata.create_all()
    session = sessionmaker(bind=engine)()

    for z, sym, name  in InitialData.elements:
        element.insert().execute(z=z, symbol=sym,  name=name)

    for units, notes  in InitialData.e_units:
        energy_units.insert().execute(units=units, notes=notes)

    for name, level in InitialData.edges:
        edge.insert().execute(name=name, level=level)

    for name, notes in InitialData.modes:
        mode.insert().execute(name=name, notes=notes)

    for name, country, city, region, fullname, lab in InitialData.facilities:
        facility.insert().execute(name=name, country=country, city=city,
                                  region=region, fullname=fullname,
                                  laboratory=lab)

    for name, notes, xray_source, fac_id in InitialData.beamlines:
        beamline.insert().execute(name=name, notes=notes,
                                  xray_source=xray_source,
                                  facility_id=fac_id)

    now = datetime.isoformat(datetime.now())
    for key, value in InitialData.info:
        if value == '<now>':
            value = now
        info.insert().execute(key=key, value=value)

    session.commit()


def dumpsql(dbname, fname='xdl_init.sql', server='sqlite'):
    """ dump SQL statements for an sqlite db"""
    if server.startswith('sqlit'):
        os.system('echo .dump | sqlite3 %s > %s' % (dbname, fname))
    else:
        os.system('pg_dump %s > %s' % (dbname, fname))

def backup_versions(fname, max=10):
    """keep backups of a file -- up to 'max', in order"""
    if os.path.exists(fname):
        for i in range(max-1, 0, -1):
            fb0 = "%s.%i" % (fname, i)
            fb1 = "%s.%i" % (fname, i+1)
            if os.path.exists(fb0):
                print ' %s -> %s ' % (fb0, fb1)
                shutil.move(fb0, fb1)
        print ' %s -> %s.1 ' % (fname, fname)
        shutil.move(fname, "%s.1" % fname)


if __name__ == '__main__':
    dbname = 'example.xdl'
    if os.path.exists(dbname):
        backup_versions(dbname)

    make_newdb(dbname, server='sqlite')
    print '''%s  created and initialized.''' % dbname
    dumpsql(dbname)

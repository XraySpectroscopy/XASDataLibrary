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
    info    = [["version", "1.2.0"],
               ["create_date", '<now>'],
               ["modify_date", '<now>']]

    e_units = [["eV", "electronVolts"],
               ["keV", "kiloelectronVolts"],
               ["degrees","angle in degrees for Bragg monochromator.  Needs mono d_spacing"] ]

    modes = [["transmission", "transmission intensity through sample"],
             ["fluorescence", "X-ray fluorescence (non-specified)"],
             ["fluorescence, total yield", "X-ray fluorescence, no energy analysis"],
             ["fluorescence, energy analyzed", "X-ray fluorescence with an energy dispersive detector"],
             ["herfd", "high-energy resolution fluorescence, with a crystal analyzer"],
             ["raman", "non-resonant X-ray inelastic scattering"],
             ["xeol", "visible or uv light emission"],
             ["electron emission", "emitted electrons from sample"],
             ["fluorescence, unitstep", "X-ray fluorescence, normalized"]]

    facilities = [
        ['SSRL',     'US',       'Palo Alto',          'Stanford Synchrotron Radiation Laboratory', 'SLAC'],
        ['NSLS',     'US',       'Upton',              'National Synchrotron Light Source', 'BNL'],
        ['NSLS-II',  'US',       'Upton',              'National Synchrotron Light Source II', 'BNL'],
        ['APS',      'US',       'Argonne',            'Advanced Photon Source', 'ANL'],
        ['ALS',      'US',       'Berkeley',           'Advanced Light Source', 'LBNL'],
        ['CAMD',     'US',       'Baton Rouge',        'Center for Advanced Microstructures and Devices', 'Louisiana State U'],
        ['CHESS',    'US',       'Ithaca',             'Cornell High Energy Synchrotron Source', 'Cornell U'],
        ['CLS',      'Canada',   'Saskatoon',          'Canadian Light Source', 'U Saskatchewan'],
        ['LNLS',     'Brasil',   'Campinas',           'Advanced Light Source', 'CNPEM'],

        ['DLS',      'UK',       'Didcot',             'Diamond Light Source', ''],
        ['SRS',      'UK',       'Cheshire',           'Synchrotron Radiation Source', 'Daresbury Laboratory'],

        ['ESRF',     'France',   'Grenoble',           'European Synchrotron Radiation Facility', ''],
        ['SOLEIL',   'France',   'GIF-sur-YVETTE',     'Synchrotron SOLEIL', '' ],
        ['ALBA',     'Spain',    'Barcelona',          'ALBA', ''],
        ['ANKA',     'Germany',  'Karlsruhe',          'Angstromquelle Karlsruhe', ''],
        ['BESSY II', 'Germany',  'Berlin',             '', ''],
        ['DAFNE',    'Italy',    'Frascati',           'DAFNE-Light','  Laboratori Nazionali di Frascati'],
        ['DELSY',    'Russia',   'Dubna',              'Dubna Electron Synchrotron', ''],
        ['SLS',      'Switzerland', 'Villingen',       'Swiss Light Source', ''],
        ['ELETTRA',  'Italy',    'Trieste',            'Elettra Synchrotron Light Laboratory', ''],
        ['PETRA III','Germany',  'Hamburg',            'DESY', ''],
        ['PETRA IV', 'Germany',  'Hamburg',            'DESY', ''],
        ['MAX IV',   'Sweden',   'Lund',               '', ''],
        ['SLRI',     'Thailand', 'Nakhon Ratchasima',  'Synchrotron Light Research Institute', 'Siam Photon'],
        ['PF',       'Japan',    'Tsukuba',            'Photon Factory', 'KEK'],
        ['AS',       'Australia', 'Victoria',          'Australia Synchrotron', ''],
        ['SESAME,',  'Jordan',   'Allaan',             'Synchrotron-light for Experimental Science and Applications in the Middle East', ''],
        ['INDUS-2',  'India',    'Indore',             '', ''],
        ['BSRF',     'China',    'Beijing',            'Beijing Synchrotron Radiation Facility', ''],
        ['NSRL',     'China',    'Hfei',               'National Synchrotron Radiation Laboratory', ''],
        ['NSRR',     'Taiwan',   'Hsinshu',            'National Synchrotron Radiation Research Center', ''],
        ['PLS',      'Korea',    'Pohang',             'Pohang Light Source',  ''],
        ['SPring-8', 'Japan',    'Hyogo',              'SPring-8',  ''],
        ['SSLS',     'Singapore',  '',                 'Singapore Synchrotron Light Source',  ''],
        ['SSRC',     'Russia',   'Novosibirsk',        'Siberian Synchrotron Research Centre', ''],
        ['SSRF',     'China',    'Shangai',            'Shanghai Synchrotron Radiation Facility',  ''],
        ]


    beamlines = [
        ['ALS 10.3.2', 'ALS', 'ALS 10.3.2', '2.5 - 17'],
        ['APS 10-BM-B', 'APS', 'APS 10-BM-B', '3 - 200'],
        ['APS 10-ID-B', 'APS', 'MRCAT', '4.3- 90'],
        ['APS 11-ID-D', 'APS', 'APS 11-ID-D', '4 - 40'],
        ['APS 12-BM-B', 'APS', 'APS 12-BM-B', '4.5 - 24'],
        ['APS 13-BM-D', 'APS', 'GSECARS', '4.5 - 70'],
        ['APS 13-ID-C,D', 'APS', 'GSECARS', '4 - 45'],
        ['APS 13-ID-E', 'APS', 'GSECARS', '2.4 - 26'],
        ['APS 16-BM-D', 'APS', 'APS 16-BM-D', '6 - 70'],
        ['APS 18-ID-D', 'APS', 'BIOCAT', '3.5 - 35'],
        ['APS 2-ID-D', 'APS', 'APS 2-ID-D', '5 - 30'],
        ['APS 20-BM-B', 'APS', 'APS 20-BM-B', '2.7- 30'],
        ['APS 20-ID-B,C', 'APS', 'APS 20-ID-B,C', '3 - 50'],
        ['APS 4-ID-C', 'APS', 'APS 4-ID-C', '0.5 - 3'],
        ['APS 4-ID-D', 'APS', 'APS 4-ID-D', '0.5 - 50'],
        ['APS 5-BM-D', 'APS', 'DNDCAT', '4.5 - 80'],
        ['APS 7-ID-B,C,D', 'APS', 'APS 7-ID-B,C,D', '6 - 21'],
        ['APS 9-BM-B,C', 'APS', 'APS 9-BM-B,C', '2.1 - 23'],

        ['CAMD DCM', 'CAMD', 'CAMD DCM', '0.9 - 20'],
        ['CLS HXMA', 'CLS', 'CLS HXMA', '5 - 40'],
        ['CLS REIXS', 'CLS', 'CLS REIXS', '0.08 - 2'],
        ['CLS SGM', 'CLS', 'CLS SGM', '0.25 - 2'],
        ['CLS SXRMB', 'CLS', 'CLS SXRMB', '1.7 - 10'],
        ['CLS VESPERS', 'CLS', 'CLS VESPERS', '6 - 30'],
        ['LNLS DXAS', 'LNLS', 'LNLS DXAS', '5 - 14'],
        ['LNLS XAFS1', 'LNLS', 'LNLS XAFS1', '4 -24'],
        ['LNLS XAFS2', 'LNLS', 'LNLS XAFS2', '4 - 17'],

        ['NSLS X10C', 'NSLS', 'NSLS X10C', '4 - 24'],
        ['NSLS X11A', 'NSLS', 'NSLS X11A', '4.5 - 40'],
        ['NSLS X11B', 'NSLS', 'NSLS X11B', '5 - 23'],
        ['NSLS X15B', 'NSLS', 'NSLS X15B', '1.2 - 8'],
        ['NSLS X18B', 'NSLS', 'NSLS X18B', '4.8 - 40'],
        ['NSLS X19A', 'NSLS', 'NSLS X19A', '2.1 - 17'],
        ['NSLS X23A2', 'NSLS', 'NSLS X23A2', '4.7 - 30'],
        ['NSLS X24A', 'NSLS', 'NSLS X24A', '1.8 - 6'],
        ['NSLS X3B', 'NSLS', 'NSLS X3B', '3.8-13.3'],

        ['SSRL 10-1', 'SSRL', 'SSRL 10-1', '0.25 - 1.2'],
        ['SSRL 10-2a', 'SSRL', 'SSRL 10-2a', '4.5 - 45'],
        ['SSRL 11-2', 'SSRL', 'SSRL 11-2', '4.5 - 37'],
        ['SSRL 13-2', 'SSRL', 'SSRL 13-2', '0.25 - 1.1'],
        ['SSRL 14-3', 'SSRL', 'SSRL 14-3', '2 - 5'],
        ['SSRL 2-3', 'SSRL', 'SSRL 2-3', '4.5 - 24'],
        ['SSRL 4-1', 'SSRL', 'SSRL 4-1', '5.5 - 38'],
        ['SSRL 4-3', 'SSRL', 'SSRL 4-3', '2.4 - 14'],
        ['SSRL 6-2a', 'SSRL', 'SSRL 6-2a', '2.3 - 17'],
        ['SSRL 7-3', 'SSRL', 'SSRL 7-3', '4.6 - 37'],
        ['SSRL 8-2', 'SSRL', 'SSRL 8-2', '0.1 - 1.3'],
        ['SSRL 9-3', 'SSRL', 'SSRL 9-3', '5 - 30'],

        ['AS XAS', 'AS', 'AS XAS', '4 - 50'],

        ['BSRF 4W1B', 'BSRF', 'BSRF 4W1B', '4 - 22'],

        ['NSRL U19', 'NSRL', 'NSRL U19', '0.01 - 0.2'],
        ['NSRL U7C', 'NSRL', 'NSRL U7C', '4 - 13'],
        ['NSRRC BL01C1', 'NSRRC', 'NSRRC BL01C1', '6 - 33'],
        ['NSRRC BL16A1', 'NSRRC', 'NSRRC BL16A1', '2 - 8'],
        ['NSRRC BL17C1', 'NSRRC', 'NSRRC BL17C1', '4.8 - 14.2'],

        ['PF AR-NW10A', 'PF', 'PF AR-NW10A', '8 - 42'],
        ['PF AR-NW14A', 'PF', 'PF AR-NW14A', '5 - 20'],
        ['PF AR-NW2A', 'PF', 'PF AR-NW2A', '5 - 20'],
        ['PF BL-11A', 'PF', 'PF BL-11A', '0.07 - 1.9'],
        ['PF BL-11B', 'PF', 'PF BL-11B', '1.7 - 5'],
        ['PF BL-12C', 'PF', 'PF BL-12C', '6 - 23'],
        ['PF BL-27B', 'PF', 'PF BL-27B', '4 - 20'],
        ['PF BL-2A', 'PF', 'PF BL-2A', '1.7 - 5'],
        ['PF BL-2C', 'PF', 'PF BL-2C', '0.25 - 1.5'],
        ['PF BL-4A', 'PF', 'PF BL-4A', '4 - 20'],
        ['PF BL-7A', 'PF', 'PF BL-7A', '0.1 - 1.5'],
        ['PF BL-7C', 'PF', 'PF BL-7C', '4 - 20'],
        ['PF BL-9A', 'PF', 'PF BL-9A', '2.1 - 15'],
        ['PF BL-9C', 'PF', 'PF BL-9C', '4 - 23'],

        ['PLS 10B', 'PLS', 'PLS 10B', '3.5 - 16'],
        ['PLS 3C1', 'PLS', 'PLS 3C1', '2.3 - 32'],
        ['PLS 7C1', 'PLS', 'PLS 7C1', '5 - 30'],
        ['PLS 8C1', 'PLS', 'PLS 8C1', '3 - 22'],

        ['SESAME A1', 'SESAME', 'SESAME A1', '3 - 30'],
        ['SLRI BL4', 'SLRI', 'SLRI BL4', '2.5 - 8'],
        ['SLRI BL8', 'SLRI', 'SLRI BL8', '1.25 - 10'],
        ['SPRING-8 BL01B1', 'SPRING-8', 'SPRING-8 BL01B1', '3.8 - 113'],
        ['SPRING-8 BL14B2', 'SPRING-8', 'SPRING-8 BL14B2', '3.8 - 72'],
        ['SPRING-8 BL28B2', 'SPRING-8', 'SPRING-8 BL28B2', '8 - 40'],
        ['SPRING-8 BL37XU', 'SPRING-8', 'SPRING-8 BL37XU', '5 - 37'],
        ['SPRING-8 BL39XU', 'SPRING-8', 'SPRING-8 BL39XU', '5 - 38'],
        ['SPRING-8 BL40XU', 'SPRING-8', 'SPRING-8 BL40XU', '8 - 17'],

        ['SSLS XDD', 'SSLS', 'SSLS XDD', '2.3 - 10'],
        ['SSRC EXAFS', 'SSRC', 'SSRC EXAFS', '.'],
        ['SSRC Soft EXAFS', 'SSRC', 'SSRC Soft EXAFS', '.'],
        ['SSRF BL08U1-A', 'SSRF', 'SSRF BL08U1-A', '0.25 - 2'],
        ['SSRF BL14W1', 'SSRF', 'SSRF BL14W1', '3.5 - 50'],

        ['ALBA CLAESS', 'ALBA', 'ALBA CLAESS', '2.4 - 65'],
        ['ANKA INE', 'ANKA', 'ANKA INE', '2.1 - 26'],
        ['ANKA SUL-X', 'ANKA', 'ANKA SUL-X', '1.5 - 22'],
        ['ANKA XAS', 'ANKA', 'ANKA XAS', '2.4 - 25'],
        ['DAFNE DXR-1', 'DAFNE', 'DAFNE DXR-1', '1.3 - 3'],
        ['Diamond B18', 'Diamond', 'Core XAFS', '2 - 35'],
        ['Diamond I06', 'Diamond', 'Nanoscience', '0.1 - 2'],
        ['Diamond I09', 'Diamond', 'Surface & Interface Structural Analysis', '0.15 - 2.1 or 2 - 20'],
        ['Diamond I10', 'Diamond', 'BLADE', '0.4 - 2'],
        ['Diamond I18', 'Diamond', 'Microfocus spectroscopy', '2 - 20'],
        ['Diamond I20', 'Diamond', 'LOLA: X-ray spectroscopy', '4 - 34'],

        ['ELETTRA ALOISA', 'ELETTRA', 'ELETTRA ALOISA', '0.12 - 2'],
        ['ELETTRA BACH', 'ELETTRA', 'ELETTRA BACH', '0.035 - 1.6'],
        ['ELETTRA BEAR', 'ELETTRA', 'ELETTRA BEAR', '0.004 - 1.4'],
        ['ELETTRA POLAR', 'ELETTRA', 'ELETTRA POLAR', '0.005 - 1'],
        ['ELETTRA TWINMIC', 'ELETTRA', 'ELETTRA TWINMIC', '0.25 - 2'],
        ['ELETTRA XAFS', 'ELETTRA', 'ELETTRA XAFS', '2.3 - 25'],
        ['ESRF BM2', 'ESRF', 'D2AM', '5 - 25'],
        ['ESRF BM20', 'ESRF', 'ROBL', '6 - 33'],
        ['ESRF BM23', 'ESRF', 'ESRF BM23', '5 - 75'],
        ['ESRF BM25A', 'ESRF', 'SPLINE', '5 - 45'],
        ['ESRF BM26A', 'ESRF', 'DUBBLE', '4 - 40'],
        ['ESRF BM30B', 'ESRF', 'FAME', '4 - 40'],
        ['ESRF BM8', 'ESRF', 'GILDA', '5 - 85'],
        ['ESRF ID08', 'ESRF', 'ESRF ID08', '0.4 - 1.5'],
        ['ESRF ID12', 'ESRF', 'ESRF ID12', '2.0 - 20'],
        ['ESRF ID21', 'ESRF', 'ESRF ID21', '0.2 - 8'],
        ['ESRF ID22', 'ESRF', 'ESRF ID22', '6.5 - 18'],
        ['ESRF ID24', 'ESRF', 'ESRF ID24', '5 - 28'],
        ['ESRF ID26', 'ESRF', 'ESRF ID26', '2.4 - 27'],

        ['MAX IV I811', 'MAX IV', 'MAX IV I811', '2.3 - 20'],
        ['PETRA III P04', 'PETRA III', 'Variable polarization XUV', '0.25 - 3'],
        ['PETRA III P06', 'PETRA III', 'Hard X-ray micro-nano probe', '2.4 - 50'],
        ['SLS MicroXAS', 'SLS', 'SLS MicroXAS', '5 - 20'],
        ['SLS SuperXAS', 'SLS', 'SLS SuperXAS', '4.5 - 35'],
        ['SOLEIL DIFFABS', 'SOLEIL', 'SOLEIL DIFFABS', '3 - 23'],
        ['SOLEIL LUCIA', 'SOLEIL', 'SOLEIL LUCIA', '0.8 - 8'],
        ['SOLEIL ODE', 'SOLEIL', 'SOLEIL ODE', '3.5 - 25'],
        ['SOLEIL PROXIMA 1', 'SOLEIL', 'SOLEIL PROXIMA 1', '5 - 15'],
        ['SOLEIL SAMBA', 'SOLEIL', 'SOLEIL SAMBA', '4 - 40'],
        ]


    edges = [["K",    "1s"],
             ["L3",   "2p3/2"],
             ["L2",   "2p1/2"],
             ["L1",   "2s"],
             ["M4,5", "3d3/2,5/2"]]

    elements = [[1,  "H",  "hydrogen"],     [2,  "He", "helium"],
                [3,  "Li", "lithium"],      [4,  "Be", "beryllium"],
                [5,  "B",  "boron"],        [6,  "C",  "carbon"],
                [7,  "N",  "nitrogen"],     [8,  "O",  "oxygen"],
                [9,  "F",  "fluorine"],     [10, "Ne", "neon"],
                [11, "Na", "sodium"],       [12, "Mg", "magnesium"],
                [13, "Al", "aluminum"],     [14, "Si", "silicon"],
                [15, "P",  "phosphorus"],   [16, "S",  "sulfur"],
                [17, "Cl", "chlorine"],     [18, "Ar", "argon"],
                [19, "K",  "potassium"],    [20, "Ca", "calcium"],
                [21, "Sc", "scandium"],     [22, "Ti", "titanium"],
                [23, "V",  "vanadium"],     [24, "Cr", "chromium"],
                [25, "Mn", "manganese"],    [26, "Fe", "iron"],
                [27, "Co", "cobalt"],       [28, "Ni", "nickel"],
                [29, "Cu", "copper"],       [30, "Zn", "zinc"],
                [31, "Ga", "gallium"],      [32, "Ge", "germanium"],
                [33, "As", "arsenic"],      [34, "Se", "selenium"],
                [35, "Br", "bromine"],      [36, "Kr", "krypton"],
                [37, "Rb", "rubidium"],     [38, "Sr", "strontium"],
                [39, "Y",  "yttrium"],      [40, "Zr", "zirconium"],
                [41, "Nb", "niobium"],      [42, "Mo", "molybdenum"],
                [43, "Tc", "technetium"],   [44, "Ru", "ruthenium"],
                [45, "Rh", "rhodium"],      [46, "Pd", "palladium"],
                [47, "Ag", "silver"],       [48, "Cd", "cadmium"],
                [49, "In", "indium"],       [50, "Sn", "tin"],
                [51, "Sb", "antimony"],     [52, "Te", "tellurium"],
                [53, "I",  "iodine"],       [54, "Xe", "xenon"],
                [55, "Cs", "cesium"],       [56, "Ba", "barium"],
                [57, "La", "lanthanum"],    [58, "Ce", "cerium"],
                [59, "Pr", "praseodymium"], [60, "Nd", "neodymium"],
                [61, "Pm", "promethium"],   [62, "Sm", "samarium"],
                [63, "Eu", "europium"],     [64, "Gd", "gadolinium"],
                [65, "Tb", "terbium"],      [66, "Dy", "dysprosium"],
                [67, "Ho", "holmium"],      [68, "Er", "erbium"],
                [69, "Tm", "thulium"],      [70, "Yb", "ytterbium"],
                [71, "Lu", "lutetium"],     [72, "Hf", "hafnium"],
                [73, "Ta", "tantalum"],     [74, "W",  "tungsten"],
                [75, "Re", "rhenium"],      [76, "Os", "osmium"],
                [77, "Ir", "iridium"],      [78, "Pt", "platinum"],
                [79, "Au", "gold"],         [80, "Hg", "mercury"],
                [81, "Tl", "thallium"],     [82, "Pb", "lead"],
                [83, "Bi", "bismuth"],      [84, "Po", "polonium"],
                [85, "At", "astatine"],     [86, "Rn", "radon"],
                [87, "Fr","francium"],      [88, "Ra", "radium"],
                [89, "Ac", "actinium"],     [90, "Th", "thorium"],
                [91, "Pa", "protactinium"], [92, "U",  "uranium"],
                [93, "Np", "neptunium"],    [94, "Pu", "plutonium"],
                [95, "Am", "americium"],    [96, "Cm", "curium"],
                [97, "Bk", "berkelium"],    [98, "Cf", "californium"],
                [99, "Es", "einsteinium"],  [100,"Fm", "fermium"],
                [101,"Md", "mendelevium"],  [102,"No", "nobelium"],
                [103,"Lw", "lawerencium"],  [104,"Rf", "rutherfordium"],
                [105,'Ha', "dubnium"],      [106,"Sg", "seaborgium"],
                [107,"Bh", "bohrium"],      [108,"Hs", "hassium"],
                [109,"Mt", "meitnerium"],   [110,"Ds", "darmstadtium"],
                [111,"Rg", "roentgenium"],  [112,"Cn", "copernicium"] ]

def  make_newdb(dbname, server= 'sqlite', user='',
                password='',  host='', port=None):
    """create initial xafs data library.  server can be
    'sqlite' or 'postgresql'
    """
    if server.startswith('sqlit'):
        engine = create_engine('sqlite:///{:s}'.format(dbname),
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
                                IntCol('reference_used'),
                                PointerCol('energy_units'),
                                PointerCol('person'),
                                PointerCol('edge'),
                                PointerCol('element', keyid='z'),
                                PointerCol('mode'),
                                PointerCol('sample'),
                                PointerCol('beamline'),
                                PointerCol('citation'),
                                PointerCol('reference_mode', 'mode'),
                                PointerCol('reference', 'sample'),
                                StrCol('rating_summary')])

    suite = NamedTable('suite', metadata,
                       cols=[PointerCol('person'),
                             StrCol('rating_summary')])

    beamline = NamedTable('beamline', metadata,
                          cols=[StrCol('xray_source'),
                                StrCol('nickname'),
                                StrCol('energy_range'),
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

    for name, country, city, fullname, lab in InitialData.facilities:
        facility.insert().execute(name=name, country=country,
                                  fullname=fullname, laboratory=lab)

    session.commit()
    for name, fac_name, nickname, erange in InitialData.beamlines:
        fac_id = None
        f = facility.select(facility.c.name == fac_name).execute().fetchall()
        if len(f) > 0:
            fac_id = f[0].id
        beamline.insert().execute(name=name, nickname=nickname, energy_range=erange, facility_id=fac_id)

    now = datetime.isoformat(datetime.now())
    for key, value in InitialData.info:
        if value == '<now>':
            value = now
        info.insert().execute(key=key, value=value)

    session.flush()
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
                print(' %s -> %s ' % (fb0, fb1))
                shutil.move(fb0, fb1)
        print(' %s -> %s.1 ' % (fname, fname))
        shutil.move(fname, "%s.1" % fname)


if __name__ == '__main__':
    dbname = 'example.xdl'
    if os.path.exists(dbname):
        backup_versions(dbname)

    make_newdb(dbname, server='sqlite')
    print('''%s  created and initialized.''' % dbname)
    dumpsql(dbname)

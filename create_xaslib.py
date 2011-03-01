#!/usr/bin/env python
#
#  This will create an empty XAS Data Library
import sys
import os

from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy import MetaData, create_engine, \
     Table, Column, Integer, Float, String, Text, DateTime, ForeignKey

def PointerCol(name, other=None, keyid='id', **kws):
    if other is None:
        other = name
    return Column("%s_%s" % (name, keyid), None,
                  ForeignKey('%s.%s' % (other, keyid), **kws))
    
def StrCol(name, size=None, **kws):
    if size is None:
        return Column(name, Text, **kws)
    else:
        return Column(name, String(size), **kws)

def NamedTable(tablename, metadata, keyid='id', nameid='name',
               name=True,notes=True, attributes=True, cols=None):
    args  = [Column(keyid, Integer, primary_key=True)]
    if name:
        args.append(StrCol(nameid, nullable=False, unique=True))
    if notes:
        args.append(StrCol('notes'))
    if attributes:
        args.append(StrCol('attributes'))
    if cols is not None:
        args.extend(cols)
    return Table(tablename, metadata, *args)

class InitialData:
    info    = [["version", "1.0.0"],
               ["creation-date", "2012-Feb-28"]]

    formats = [["internal-json", "Read data_* values of spectra table as json"],
               ["external-xdi",  "Read data from extenal XDI formatted file"]]

    e_units = [["eV", "electronVolts"],
               ["keV", "kiloelectronVolts"],
               ["degrees","angle in degrees for Bragg Monochromator.  Need mono dspacing to convert to eV"],
               ["steps",  "angular steps for Bragg Monochromator. Need mono dspacing and steps_per_degree to convert to eV"]]
    
    modes = [["transmission", "transmission intensity through sample"],
             ["fluorescence, total yield", "total x-ray fluorescence intensity, no energy analysis"],
             ["fluorescence, energy analyzed", '''x-ray fluorescence measured with an energy dispersive (solid-state) detector.
 Measurements will often need to be corrected for dead-time effects'''],
             ["xeol", "visible or uv light emission"],
             ["electron emission", "emitted electrons from sample"]]

    
    edges = [["K", "1s"], ["L3", "2p3/2"], ["L2", "2p1/2"], ["L1", "2s"]]
    
    elements = [[1, "H", "hydrogen"], [2, "He", "helium"], [3, "Li","lithium"],
            [4, "Be", "beryllium"], [5, "B", "boron"], [6, "C", "carbon"],
            [7, "N", "nitrogen"], [8, "O", "oxygen"], [9, "F", "fluorine"],
            [10, "Ne", "neon"], [11, "Na", "sodium"], [12, "Mg", "magnesium"],
            [13, "Al", "aluminum"], [14, "Si", "silicon"], [15, "P", "phosphorus"],
            [16, "S", "sulfur"], [17, "Cl", "chlorine"], [18, "Ar", "argon"],
            [19, "K", "potassium"], [20, "Ca", "calcium"], [21, "Sc", "scandium"],
            [22, "Ti","titanium"], [23, "V", "vanadium"], [24, "Cr", "chromium"],
            [25, "Mn","manganese"], [26, "Fe", "iron"], [27, "Co", "cobalt"],
            [28, "Ni","nickel"], [29, "Cu", "copper"], [30, "Zn", "zinc"],
            [31, "Ga", "gallium"],[32, "Ge", "germanium"], [33, "As", "arsenic"],
            [34, "Se", "selenium"],[35, "Br", "bromine"], [36, "Kr", "krypton"],
            [37, "Rb", "rubidium"], [38,"Sr", "strontium"], [39, "Y", "yttrium"],
            [40, "Zr", "zirconium"], [41, "Nb", "niobium"], [42, "Mo", "molybdenum"],
            [43, "Tc", "technetium"], [44, "Ru", "ruthenium"], [45, "Rh", "rhodium"],
            [46, "Pd", "palladium"], [47, "Ag", "silver"], [48, "Cd", "cadmium"],
            [49, "In", "indium"], [50, "Sn", "tin"], [51, "Sb", "antimony"],
            [52, "Te", "tellurium"], [53, "I", "iodine"], [54, "Xe", "xenon"],
            [55, "Cs", "cesium"], [56, "Ba", "barium"], [57, "La", "lanthanum"],
            [58, "Ce", "cerium"], [59, "Pr", "praseodymium"],[60, "Nd", "neodymium"],
            [61, "Pm", "promethium"], [62, "Sm", "samarium"], [63, "Eu", "europium"],
            [64, "Gd", "gadolinium"], [65, "Tb", "terbium"], [66, "Dy", "dysprosium"],
            [67, "Ho", "holmium"], [68, "Er", "erbium"], [69, "Tm", "thulium"],
            [70, "Yb", "ytterbium"], [71, "Lu", "lutetium"], [72,"Hf", "hafnium"],
            [73, "Ta", "tantalum"], [74, "W", "tungsten"], [75, "Re","rhenium"],
            [76, "Os", "osmium"], [77, "Ir", "iridium"], [78, "Pt", "platinum"],
            [79, "Au", "gold"], [80, "Hg", "mercury"], [81, "Tl", "thallium"],
                [82, "Pb", "lead"], [83, "Bi", "bismuth"], [84, "Po","polonium"],
                [85, "At", "astatine"], [86, "Rn", "radon"], [87, "Fr","francium"],
                [88, "Ra", "radium"], [89, "Ac", "actinium"], [90, "Th","thorium"],
                [91, "Pa", "protactinium"], [92, "U", "uranium"], [93, "Np","neptunium"],
                [94, "Pu", "plutonium"], [95, "Am", "americium"], [96, "Cm", "curium"],
                [97, "Bk", "berkelium"], [98, "Cf", "californium"], [99, "Es", "einsteinium"],
                [100, "Fm", "fermium"], [101, "Md", "mendelevium"], [102, "No", "nobelium"],
                [103, "Lw", "lawerencium"], [104, "Rf", "Rutherfordium"], [105, 'Ha', "Dubnium"],
                [106, "Sg", "Seaborgium"], [107, "Bh", "Bohrium"], [108, "Hs", "Hassium"], 
                [109, "Mt", "Meitnerium"]
                ]

                

def  make_newdb(dbname, server= 'sqlite', overwrite=False):
    if os.path.exists(dbname) and not overwrite:
        print '%s exists and will not be overwritten' % dbname
        return False
    
    engine  = create_engine('%s:///%s' % (server, dbname))
    metadata =  MetaData(engine)

    format  = NamedTable('format', metadata)
    
    ligand  = NamedTable('ligand', metadata)
    mode    = NamedTable('mode', metadata)
    facility = NamedTable('facility', metadata)
    
    element = NamedTable('element', metadata, keyid='z',
                         notes=False, attributes=False,
                         cols=[StrCol('symbol', size=2,
                                      unique=True,
                                      nullable=False)])
    
    edge = NamedTable('edge', metadata,
                      notes=False, attributes=False,
                      cols=[StrCol('level', size=32,
                                   unique=True, nullable=False)])

    energy_units = NamedTable('energy_units', metadata, nameid='units')

    mono = NamedTable('monochromator', metadata,
                      cols=[Column('lattice_constant', Float(precision=8)),
                            Column('steps_per_degree', Float(precision=8)),
                            PointerCol('energy_units')])
    
    crystal_structure = NamedTable('crystal_structure', metadata,
                         cols=[StrCol('format'), 
                               StrCol('data')])
    
    person = NamedTable('person', metadata, nameid='email',
                        cols=[StrCol('firstname', nullable=False),
                              StrCol('lastname', nullable=False),
                              StrCol('affiliation')])
    
    citation = NamedTable('citation', metadata, 
                          cols=[StrCol('journal'),
                                StrCol('authors'),
                                StrCol('title'),
                                StrCol('volume'),
                                StrCol('pages'),
                                StrCol('year'),
                                StrCol('doi')])
    
    sample = NamedTable('sample', metadata, 
                        cols=[StrCol('formula'),
                              StrCol('material_source'),
                              PointerCol('person'),
                              PointerCol('crystal_structure')])
    
    scols = [StrCol('file_link'),
             StrCol('data_energy'),
             StrCol('data_i0', server_default='[1.0]'),
             StrCol('data_itrans', server_default='[1.0]'),
             StrCol('data_iemit', server_default='[1.0]'),
             StrCol('data_irefer', server_default='[1.0]'),
             StrCol('data_dtime_corr', server_default='[1.0]'),
             StrCol('calc_mu_trans', server_default='-log(itrans/i0)'),
             StrCol('calc_mu_emit',  server_default='(iemit*dtime_corr/i0)'),
             StrCol('calc_mu_refer', server_default='-log(irefer/itrans)'),
             StrCol('notes_i0'),
             StrCol('notes_itrans'),
             StrCol('notes_iemit'),
             StrCol('notes_irefer'),
             StrCol('temperature'),
             Column('submission_date', DateTime),
             Column('collection_date', DateTime),
             Column('reference_used', Integer), # , server_default=0),
             PointerCol('energy_units'),
             PointerCol('monochromator'),
             PointerCol('person'),
             PointerCol('edge'),
             PointerCol('element',keyid='z'),
             PointerCol('sample'),
             PointerCol('beamline'),
             PointerCol('format'),
             PointerCol('citation'),
             PointerCol('reference', 'sample')]
    
    spectra = NamedTable('spectra', metadata,
                         cols=scols)
    
    
    suite = NamedTable('suite', metadata, 
                       cols=[PointerCol('person')])
    
    
    beamline = NamedTable('beamline', metadata, 
                          cols=[StrCol('xray_source'),
                                PointerCol('monochromator'),
                                PointerCol('facility'),
                                ])
    
    
    spectra_rating = Table('spectra_rating', metadata,
                           Column('id', Integer, primary_key=True), 
                           Column('score', Integer),
                           StrCol('comments'),
                           PointerCol('person') ,
                           PointerCol('spectra'))

    suite_rating = Table('suite_rating', metadata,
                           Column('id', Integer, primary_key=True), 
                           Column('score', Integer),
                           StrCol('comments'),
                           PointerCol('person') ,                         
                           PointerCol('suite'))
    
    spectra_suite = Table('spectra_suite', metadata,
                          Column('id', Integer, primary_key=True), 
                          PointerCol('suite') ,
                          PointerCol('spectra'))

    spectra_mode = Table('spectra_mode', metadata,
                         Column('id', Integer, primary_key=True), 
                         PointerCol('mode') ,
                         PointerCol('spectra'))
    
    spectra_ligand = Table('spectra_ligand', metadata,
                           Column('id', Integer, primary_key=True), 
                           PointerCol('ligand'),
                           PointerCol('spectra'))                                    

    info = Table('info', metadata,
                 Column('key', Text, primary_key=True, unique=True), 
                 StrCol('value'))

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

    for name, notes in InitialData.formats:
        format.insert().execute(name=name, notes=notes)

    for key, value in InitialData.info:
        info.insert().execute(key=key, value=value)

    session.commit()    
    return True

               
if __name__ == '__main__':
    dbname = 'xasdat.sqlite'
    if len(sys.argv) > 1:
        dbame  = sys.argv[1]
    if make_newdb(dbname, overwrite=True):
        print '''%s  created and initialized.''' % dbname

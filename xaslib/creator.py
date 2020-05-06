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
from sqlalchemy import (MetaData, create_engine, Table, Column, Integer,
                        Float, String, Text, DateTime, ForeignKey)

from sqlalchemy.pool import SingletonThreadPool

from . import initialdata

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


def create_xaslib(dbname, server= 'sqlite', user='',
                password='',  host='', port=None):
    """create and initialize a new XAS data library.  server can be
    'sqlite' or 'postgresql'
    """
    if server.startswith('sqlit'):
        engine = create_engine('sqlite:///{:s}'.format(dbname),
                               poolclass=SingletonThreadPool)
    else: # postgres
        conn_str= 'postgresql://%s:%s@%s:%d/%s'
        if port is None:
            port = 5432

        dbname = dbname.lower()
        # first we check if dbname exists....
        try:
            query = "select datname from pg_database"
            pg_engine = create_engine(conn_str % (user, password,
                                                  host, port, 'postgres'))
            conn = pg_engine.connect()
            conn.execution_options(autocommit=True)
            conn.execute("commit")
            dbs = [i[0].lower() for i in conn.execute(query).fetchall()]
            if dbname not in dbs:
                conn.execute("create database %s" % dbname)
                conn.execute("commit")
            conn.close()
            time.sleep(0.5)
        except:
            pass

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
                              StrCol('confirmed'),
                              IntCol('admin_level')])

    citation = NamedTable('citation', metadata,
                          cols=[StrCol('journal'),
                                StrCol('authors'),
                                StrCol('title'),
                                StrCol('volume'),
                                StrCol('pages'),
                                StrCol('year'),
                                StrCol('doi'),
                                PointerCol('person'),
                                ])

    sample = NamedTable('sample', metadata, name_unique=False,
                        cols=[StrCol('formula'),
                              StrCol('material_source'),
                              StrCol('preparation'),
                              PointerCol('person'),
                              PointerCol('crystal_structure')
                              ])

    spectrum = NamedTable('spectrum', metadata, name_unique=False,
                          cols=[StrCol('energy'),
                                StrCol('description'),
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

    spectrum_ligand = Table('spectrum_ligand', metadata,
                           IntCol('id', primary_key=True),
                           PointerCol('ligand'),
                           PointerCol('spectrum'))

    metadata.create_all()
    session = sessionmaker(bind=engine)()

    for z, sym, name  in initialdata.elements:
        element.insert().execute(z=z, symbol=sym,  name=name)

    for units, notes  in initialdata.e_units:
        energy_units.insert().execute(units=units, notes=notes)

    for name, level in initialdata.edges:
        edge.insert().execute(name=name, level=level)

    for name, notes in initialdata.modes:
        mode.insert().execute(name=name, notes=notes)

    for name, country, city, fullname, lab in initialdata.facilities:
        facility.insert().execute(name=name, country=country, city=city,
                                  fullname=fullname, laboratory=lab)

    session.commit()
    for name, fac_name, nickname, erange in initialdata.beamlines:
        fac_id = None
        f = facility.select(facility.c.name==fac_name).execute().fetchall()
        if len(f) > 0:
            fac_id = f[0].id
        beamline.insert().execute(name=name, nickname=nickname,
                                  energy_range=erange, facility_id=fac_id)

    now = datetime.isoformat(datetime.now())
    for key, value in initialdata.info:
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

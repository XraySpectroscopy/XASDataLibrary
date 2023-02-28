#!/usr/bin/env python
"""
Principle Python interface to XAS Data Library
requires SQLAlchemy 0.6 or higher

Main Class:  XASDataLibrary

"""

import os
import sys
import time
import random
import json
import logging
import numpy as np
from datetime import datetime

from base64 import b64encode
from hashlib import pbkdf2_hmac

from sqlalchemy import MetaData, create_engine, text, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

from larch.io import XDIFile, read_ascii
from larch.utils import debugtime

from . import initialdata
from .simpledb import (SimpleDB, isSimpleDB, isotime,
                       hash_password, test_password)


def isXASDataLibrary(dbname):
    """test if a file is a valid XAS Data Library file:
       must be a sqlite db file, with tables named
          'info', 'spectra', 'element' and 'energy_units'
       the 'element' table must have more than 90 rows and the
       'info' table must have an entries named 'version' and 'create_date'
    """
    return isSimpeleDB(dbname, required_tables=('info', 'spectra',
                                                'elements', 'energy_units'))


def json_encode(val):
    "simple wrapper around json.dumps"
    if val is None or isinstance(val, str):
        return val
    if isinstance(val, np.ndarray):
        val = val.flatten().tolist()
    return  json.dumps(val)

def valid_score(score, smin=0, smax=5):
    """ensure that the input score is an integr
    in the range [smin, smax]  (inclusive)"""
    return max(smin, min(smax, int(score)))

def unique_name(name, namelist, maxcount=100, msg='spectrum'):
    """
    find a name that is not in namelist by making
       name (1),  name (2), etc
    up to maxcount, at which point an exception is raised.
    """
    basename, count = name, 0
    while name in namelist:
        count += 1
        if count > maxcount:
            msg = "a %s named '%s' already exists"  % (msg, name)
            raise ValueError(msg)
        name = "%s (%d)" % (basename, count)
    return name

def isotime2datetime(intime):
    sdate, stime = intime.replace('T', ' ').split(' ')
    syear, smon, sday = [int(x) for x in sdate.split('-')]
    sfrac = '0'
    if '.' in stime:
        stime, sfrac = stime.split('.')
    shour, smin, ssec  = [int(x) for x in stime.split(':')]
    susec = int(1e6*float('.%s' % sfrac))
    return datetime(syear, smon, sday, shour, smin, ssec, susec)

def guess_datetime(tstring):
    if 'T' in tstring and 'OCT' not in tstring:
        tstring = tstring.replace('T', ' ')

    for dfmt in ("%Y-%m-%d", "%Y-%b-%d", "%Y/%m/%d", "%Y/%b/%d",
                 "%b %d, %Y", "%m/%d/%Y", "%d/%m/%Y"):
        for tfmt in ("%H:%M:%S", "%H:%M"):
            dtfmt = "%s %s" % (dfmt, tfmt)
            try:
                out = datetime.strptime(tstring, dtfmt)
            except ValueError:
                out = None
            if out is not None:
                return out

class XASDataLibrary(SimpleDB):
    """full interface to XAS Spectral Library"""

    def __init__(self, dbname=None, server= 'sqlite', user='', password='',
                 host='', port=5432, dialect=None, logfile=None):

        SimpleDB.__init__(self, dbname=dbname, server=server, user=user,
                          password=password, host=host, port=port, dialect=dialect,
                          logfile=logfile)

        self.session = None

    def included_elements(self, retval='symbol'):
        """return a list of elements with one or more spectra"""
        zvals = []
        for s in self.get_rows('spectrum'):
            ez = s.element_z
            if ez not in zvals:
                zvals.append(ez)
        out = []
        for z, atsym, name in initialdata.elements:
            if z in  zvals:
                val = z
                if retval == 'symbol':
                    val = atsym
                elif retval ==  'name':
                    val = name
                out.append(val)
        return out

    def get_facility(self,  facility):
        """return facility or list of facilities"""
        return self.get_rows('facility', where={'name': facility},
                             limit_one=True, none_if_empty=True)

    def get_facilities(self, order_by='id'):
        """return facility or list of facilities"""
        return self.get_rows('facility', order_by=order_by, none_if_empty=True)

    def get_element(self, val):
        """return element z, name, symbol from one of z, name, symbol"""
        key = 'symbol'
        if isinstance(val, int):
            key = 'z'
        elif len(val) > 2:
            key = 'name'
        kws = {key: val}
        return self.get_rows('element', where=kws, limit_one=True, none_if_empty=True)

    def get_elements(self):
        """return list of elements z, name, symbol"""
        return self.get_rows('element')

    def get_modes(self):
        """return list of measurement modes"""
        return self.get_rows('mode')

    def get_edge(self, val, key='name'):
        """return edge by name  or id"""
        if isinstance(val, int):
            key = 'id'
        return self.get_rows('edge', where={key: val}, limit_one=True, none_if_empty=True)

    def get_edges(self):
        """return list of edges"""
        return self.get_rows('edge')

    def get_beamline(self, val, key='name'):
        """return beamline by name  or id"""
        if isinstance(val, int):
            key = 'id'
        kws = {key: val}
        return self.get_rows('beamline', where={key: val}, limit_one=True, none_if_empty=True)

    def add_energy_units(self, units, notes=None, **kws):
        """add Energy Units: units required
        notes  optional
        returns EnergyUnits instance"""
        return self.add_row('energy_units', units=units, notes=notes, **kws)

    def get_sample(self, sid):
        """return sample by id"""
        return self.get_rows('sample', where={'id': sid}, limit_one=True, none_if_empty=True)

    def add_mode(self, name, notes='', **kws):
        """add collection mode: name required"""
        return self.add_row('mode', name=name, notes=notes, **kws)

    def add_crystal_structure(self, name, notes='', data=None, **kws):
         """add data format: name required"""
         kws.updata(dict(name=name, notes=notes,  data=data))
         return self.add_row('crystal_structure', **kws)

    def add_edge(self, name, level):
        """add edge: name and level required"""
        return self.add_row('edge', name=name, level=level)

    def add_facility(self, name, notes='', **kws):
        """add facilty by name, return Facility instance"""
        kws.updata(dict(name=name, notes=notes))
        return self.add_row('facility', **kws)

    def add_beamline(self, name, facility_id=None, notes='', **kws):
        """add beamline by name, with facility id"""
        kws.updata(dict(name=name, notes=notes, facility_id=facility_id))
        return self.add_row('beamline', **kws)

    def add_citation(self, name, **kws):
        """add literature citation: name required"""
        return self.add_row('citation', name=name, **kws)

    def add_info(self, key, value):
        """add Info key value pair"""
        return self.add_row('info', key=key, value=value)

    def add_ligand(self, name, **kws):
        """add ligand: name required"""
        return self.add_row('ligand', name=name, **kws)

    def add_person(self, name, email, affiliation='', password=None,
                   confirmed='false', **kws):
        """add person: arguments are  name, email with optional affiliation and password"""

        kws.update(dict(affiliation=affiliation))
        self.add_row('person', email=email, name=name, **kws)
        if password is not None:
            self.set_person_password(email, password, confirmed=confirmed)

    def get_person(self, val, key='email'):
        """get person by email"""
        if isinstance(val, int):
            key = 'id'
        return self.get_rows('person', where={key: val}, limit_one=True, none_if_empty=True)

    def get_persons(self, **kws):
        """return list of people"""
        return self.get_rows('person', where=kws)

    def set_person_password(self, email, password, confirmed=None, auto_confirm=False):
        """ set secure password for person"""
        hash = hash_password(password)
        if confirmed is None:
            confirmed = 'true' if auto_confirm else 'false'
        else:
            confirmed = 'true' if confirmed else 'false'

        self.update('person', where={'email': email}, password=hash,
                    confirmed=confirmed)

    def test_person_password(self, email, password):
        """test password for person, returns True if valid"""
        row = self._get_person_by_email(email)
        return test_password(password, row.hash, minimum_runtime=0.05)

    def test_person_confirmed(self, email):
        """test if account for a person is confirmed"""
        row = self.get_person(email)
        return row.confirmed.lower() == 'true'

    def person_unconfirm(self, email):
        """ sets a person to 'unconfirmed' status, pending confirmation,
        returns hash, which must be used to confirm person"""
        hash = b64encode(os.urandom(24)).decode('utf-8').replace('/', '_')
        self.update('person', where={'email': email}, confirmed=hash)
        return hash

    def person_test_confirmhash(self, email, hash):
        """test if a person's confirmation hash is correct"""
        return (self.get_person(email).confirmed == hash)

    def person_confirm(self, email, hash):
        """try to confirm a person,
        test the supplied hash for confirmation,
        setting 'confirmed' to 'true' if correct.
        """
        confirmed = (hash == self.get_person(email).confirmed)
        if confirmed:
            self.update('person', where={'email': email}, confirmed='true')
        return confirmed

    def add_sample(self, name, person_id, **kws):
        "add sample: name required returns sample id"
        return self.add_row('sample', name=name, person_id=person_id, **kws)

    def add_suite(self, name, notes='', person_id=None, **kws):
        """add suite: name required
        returns Suite instance"""
        return self.add_row('suite', name=name, notes=notes,
                            person_id=person_id, **kws)

    def del_suite(self, suite_id):
        self.delete_rows('suite', {'id': suite_id})
        self.delete_rows('suite_rating', {'id': suite_id})
        self.delete_rows('spectrum_suite', {'suite_id': suite_id})


    def remove_spectrum_from_suite(self, suite_id, spectrum_id):
        self.delete_rows('spectrum_suite', {'suite_id': suite_id,
                                            'spectrum_id': spectrum_id})

    def del_spectrum(self, sid):
        self.delete_rows('spectrum', {'id:', sid})
        self.delete_rows('spectrum_rating', {'id:', sid})
        self.delete_rows('spectrum_suite', {'spectrum_id:', sid})


    def set_suite_rating(self, person_id, suite_id, score, comments=None):
        """add a rating score to a suite, also update summary rating"""
        if comments is None:
            comments = ''

        vals = {'score': valid_score(score),
               'datetime': datetime.now(),
               'comments':comments}
        where={'suite_id': suite_id, 'person_id': person_id},

        row = self.get_rows('suite_rating', where=where, none_if_empty=True)
        if rows is None:
            vals.update(where)
            self.add_row('suite_rating', **vals)
        else:
            self.update('suite_rating', where=where, **vals)

        # recompute average rating for suite
        sum = 0.0
        for row in self.get_rows('suite_rating', where={'suite_id': suite_id}):
            sum += 1.0*float(row.score)

        rating = 'No ratings'
        if len(rows) > 0:
            rating = '%.1f (%d ratings)' % (sum/len(rows), len(rows))
        self.update('suite', where=where, rating_summary=rating)


    def set_spectrum_rating(self, person_id, spectrum_id, score, comments=None):
        """add a score to a spectrum: person_id, spectrum_id, score, comment
        score is an integer value 0 to 5"""
        if comments is not None:
            comments = ''
        valss = {'score': valid_score(score),
                 'datetime': datetime.now(),
                 'comments': comments}
        where = {'spectrum_id': spectrum_id, 'person_id': person_id}


        row = self.get_rows('spectrum_rating', where=where, none_if_empty=True)
        if rows is None:
            vals.update(where)
            self.add_row('spectrum_rating', **vals)
        else:
            self.update('spectrum_rating', where=where, **vals)

        # recompute average rating for spectrum
        sum = 0.0
        for row in self.get_rows('suite_rating', where={'spectrum_id': spectrum_id}):
            sum += 1.0*float(row.score)

        rating = 'No ratings'
        if len(rows) > 0:
            rating = '%.1f (%d ratings)' % (sum/len(rows), len(rows))
        self.update('spectrum', where=where, rating_summary=rating)


    def add_spectrum(self, name, description=None, notes='', d_spacing=-1,
                     energy_units=None, edge='K', element=None,
                     mode='transmission', reference_sample='none',
                     reference_mode='transmission', temperature=None,
                     energy=None, i0=None, itrans=None, ifluor=None,
                     irefer=None, energy_stderr=None, i0_stderr=None,
                     itrans_stderr=None, ifluor_stderr=None,
                     irefer_stderr=None, energy_notes='', i0_notes='',
                     itrans_notes='', ifluor_notes='', irefer_notes='',
                     submission_date=None, collection_date=None, person=None,
                     sample=None, beamline=None, citation=None, **kws):

        """add spectrum: name required
        returns Spectrum instance"""
        spectrum_names = [s.name for s in self.get_rows('spectrum')]

        if name in spectrum_names:
            raise ValueError(f"a spectrum named '{name}' already exists")

        if description is None:
            description = name
        dlocal = locals()

        # simple values
        for attr in ('name', 'description', 'notes', 'd_spacing', 'reference_sample',
                     'temperature', 'energy_notes', 'i0_notes',
                     'itrans_notes', 'ifluor_notes', 'irefer_notes'):
            kws[attr] = dlocal.get(attr, '')

        # arrays
        for attr in ('energy', 'i0', 'itrans', 'ifluor', 'irefer',
                     'energy_stderr', 'i0_stderr', 'itrans_stderr',
                     'ifluor_stderr', 'irefer_stderr'):
            val = ''
            if dlocal[attr] is not None:
                val = json_encode(dlocal.get(attr, ''))
            kws[attr] = val

        # simple pointers
        for attr in ('person', 'sample', 'citation'):
            kws['%s_id' % attr] = dlocal.get(attr, '')

        # dates
        if submission_date is None:
            submission_date = datetime.now()
        for attr, val in (('submission_date', submission_date),
                          ('collection_date', collection_date)):
            if isinstance(val, str):
                try:
                    val = isotime2datetime(val)
                except ValueError:
                    val = None
            if val is None:
                val = datetime(1, 1, 1)
            kws[attr] = val

        # more complicated foreign keys, pointers to other tables

        bline = self.guess_beamline(beamline)
        if bline is not None:
            kws['beamline_id'] = bline.id

        if bline is None:
            print("Add Spectrum : No beamline found = ",name,  beamline)

        kws['edge_id'] = self.get_edge(edge).id
        kws['mode_id'] = self.lookup('mode', name=mode)[0].id
        if irefer is None:
            reference_mode = 'none'
        try:
            kws['reference_mode_id'] = self.lookup('reference_mode', name=reference_mode)[0].id
        except:
            kws['reference_mode_id'] = 0
        kws['element_z'] = self.get_element(element).z
        kws['energy_units_id'] = self.lookup('energy_units', name=energy_units)[0].id
        return self.add_row('spectrum',   **kws)

    def get_beamlines(self, facility=None, order_by='id'):
        """get all beamlines for a facility
        Parameters
        --------
        facility  id or name of facility, or None for all facilities

        Returns
        -------
        list of matching beamlines

        """
        where = {}
        if facility is not None:
            fwhere  = {}
            if isinstance(facility, int):
                fwhere = {'id': facility}
            elif isinstance(facility, str):
                fwhere = {'name': facility}

            fac_id = None
            row = self.get_rows('facility', where=fwhere, limit_one=True, none_if_empty=True)
            print(" FAC ", fwhere)
            if row is not None:
                where = {'facility_id': row.id}


        return self.get_rows('beamline', where=where, order_by=order_by)

    def get_beamline_list(self, order_by='name', with_any=False):
        """ get list or beamline dicts with facility info included"""
        out = []
        if with_any:
            out.append({'id': '0', 'name': 'Any', 'notes': '',
                        'xray_source':'', 'fac_name': '', 'fac_loc': ''})

        facs = {}
        for row in self.lookup('facility'):
            facs[row.id] = row
        for row in self.get_beamlines(order_by=order_by):
            fac  = facs[row.facility_id]
            loc = fac.country
            if fac.city is not None and len(fac.city) > 0:
                loc = "%s, %s" % (fac.city, fac.country)
            out.append({'id': '%d' % row.id,
                        'name': row.name,
                        'notes': row.notes,
                        'xray_source': row.xray_source,
                        'fac_name': fac.name,
                        'fac_loc': loc})
        return out


    def guess_beamline(self, name, facility=None):
        """return best guess of beamline by name"""
        bline = self.get_rows('beamline', where={'name':name}, none_if_empty=True, limit_one=True)
        if bline is not None:
            return bline

        candidates = self.get_beamlines(facility=facility)
        lname = name.lower()
        for b in candidates:
            if lname in b.name.lower() or lname in b.nickname.lower():
                return b

        if '(' in lname:
            lname = lname.split('(')[0].strip()
        for b in candidates:
            if lname in b.name.lower() or lname in b.nickname.lower():
                return b

        def clean_name(s):
            s = s.lower()
            for c in '-_ & ': s = s.replace(c, '')
            return s

        lname = clean_name(lname)

        for b in candidates:
            name = clean_name(b.name)
            nickname = clean_name(b.nickname)
            if lname in name or lname in nickname:
                return b
        return None

    def get_suite_ratings(self, suite):
        "get all ratings for a suite"
        if hasattr(suite, 'id') and hasattr(suite, 'rating_summary'):
            suite_id = suite_id.id
        elif isinstance(suite, int):
            suite_id = suite
        return self.lookup('suite_rating', suite_id=suite_id)

    def get_spectrum_ratings(self, spectrum):
        "get all ratings for a spectrum"
        if hasattr(spectrum, 'id') and hasattr(spectrum, 'itrans'):
            sid = spectrum.id
        elif isinstance(spectrum, int):

            sid = spectrum
        return self.lookup('spectrum_rating', spectrum_id=sid)

    def get_spectrum(self, spectrum_id):
        return self.get_rows('spectrum', where={'id':spectrum_id},
                             limit_one=True, none_if_empty=True)


    def get_spectrum_mode(self, spectrum_id):
        """return name of mode for a spectrum"""
        spect = self.get_spectrum(spectrum_id)
        if spect is not None:
            mode_id = spect.mode_id
            return self.lookup('mode', id=mode_id)[0].name

    def get_spectrum_refmode(self, spectrum_id):
        """return name of refernce mode for a spectrum"""
        spect = self.get_spectrum(spectrum_id)
        if spect is not None:
            mode_id = spect.reference_mode_id
            return self.lookup('reference_mode', id=mode_id)[0].name

    def get_spectrum_beamline(self, spectrum_id):
        "return id, desc for beamline for aa spectrum"
        blid, desc  = -1, 'unknown'
        spect = self.get_spectrum(spectrum_id)
        if spect is not None:
            bl = self.lookup('beamline', id=spect.beamline_id)[0]
            if bl is not None:
                blid = bl.id
                desc = bl.name
        if (blid is None or blid < 0) and (spect.notes is not None):
            tname = spect.notes.get('beamline', {}).get('name', None)
            if tname is not None:
                desc = "may be '%s'" % (desc, tname)
        return '%d' % blid, desc


    # done through here, I think

    def get_spectra(self, edge=None, element=None, beamline=None,
                    person=None, mode=None, facility=None,
                    # sample=None, suite=None, citation=None, ligand=None,
                    order_by='id'):
        """get all spectra matching some set of criteria

        Parameters
        ----------
        edge       by Name
        element    by Z, Symbol, or Name
        person     by email
        beamline   by name
        facility
        mode
        # sample
        # citation
        # ligand
        # suite
        """
        where = {}
        def getval(row, key='id', default=None):
            if row is None:
                return default
            return getattr(row, key, default)

        # edge
        if edge is not None:
            where['edge_id'] = getval(self.get_edge(edge))

        # element
        if element is not None:
            where['element_z'] = getval(self.get_element(element), key='z')

        # beamline
        if beamline is not None:
            where['beamline_id'] = getval(self.get_beamline(name=beamline))

        # person
        if person is not None:
            where['person_id'] = getval(self.get_person(person))

        # mode
        if mode is not None:
            where['mode_id'] = getval(self.get_mode(mode))

        results = self.get_rows('spectrum', where=where, order_by=order_by)

        # facility filter is post-query
        if facility is not None:
            bl_ids = [bl.id for bl in self.get_beamlines(facility=facility)]
            results = [row for row in results if row.beamline_id in bl_ids]

        return results


    def add_xdifile(self, fname, spectrum_name=None, description=None,
                    person=None, reuse_sample=True, mode=None, commit=True,
                    verbose=False, **kws):

        try:
            fh  = open(fname, 'r')
            filetext  = fh.read()
        except:
            filetext = ''
        finally:
            fh.close()

        xfile = XDIFile(fname)
        try:
            afile = read_ascii(fname)
        except:
            afile = None

        path, fname = os.path.split(fname)
        now = isotime()

        if spectrum_name is None:
            spectrum_name = fname
        if spectrum_name.endswith('.xdi'):
            spectrum_name = spectrum_name[:-4]

        if description is None:
            description  = spectrum_name


        all_spect_names = [s.name for s in self.get_rows('spectrum')]
        spectrum_name = unique_name(spectrum_name, all_spect_names)

        try:
            c_date = xfile.attrs['scan']['start_time']
        except:
            c_date = 'collection date unknown'
        d_spacing = xfile.dspacing
        energy    = xfile.energy
        edge      = xfile.edge.decode('utf-8')
        element   = xfile.element.decode('utf-8')
        comments  = ''
        if hasattr(xfile, 'comments'):
            comments = xfile.comments.decode('utf-8')
        # prefer to get comments from original header, if possible
        header = getattr(afile, 'header', None)
        if header is not None:
            comment_lines = []
            slashes_found = False
            for hline in header:
                hline = hline.strip()
                if slashes_found:
                    if hline.startswith('#'):
                        hline = hline[1:].strip()
                    if len(hline) > 0:
                        comment_lines.append(hline)
                slashes_found = hline.startswith('# //')
                if hline.startswith('#---'):
                    break
            if len(comment_lines) > 0:
                comments = '\n'.join(comment_lines)

        i0  = getattr(xfile, 'i0', getattr(xfile, 'io', np.ones(len(energy))*1.0))

        itrans = getattr(xfile, 'itrans', getattr(xfile, 'i1', None))
        ifluor = getattr(xfile, 'ifluor', getattr(xfile, 'if', None))
        irefer = getattr(xfile, 'irefer', getattr(xfile, 'i2', None))

        if hasattr(xfile, 'mutrans'):
            itrans = i0 * np.exp(-xfile.mutrans)
        if hasattr(xfile, 'mufluor'):
            ifluor = i0 * xfile.mufluor

        if mode is None:
            mode = 'fluorescence'
            if itrans is not None:
                mode = 'transmission'
        if mode == 'transmission' and itrans is None:
            raise ValueError("cannot find transmission data")
        elif mode == 'fluoresence' and ifluor is None:
            raise ValueError("cannot find fluorescence data")

        reference_mode = 'none' if irefer is None else 'transmission'

        en_units = 'eV'
        for index, value in xfile.attrs['column'].items():
            words = value.split()
            if len(words) > 1:
                if (value.lower().startswith('energy') or
                    value.lower().startswith('angle') ):
                    en_units = words[1]

        if person is not None:
            person_id = self.get_person(person).id

        beamline = None
        temperature = None
        reference_sample = None
        sample_id = 0
        if 'sample' in xfile.attrs:
            sample_attrs  = xfile.attrs['sample']
            if 'temperature' in sample_attrs:
                temperature = sample_attrs['temperature']
            if 'name' in sample_attrs:
                sample_name = sample_attrs.pop('name')

            if 'reference' in sample_attrs:
                reference_sample = sample_attrs['reference']

            sample_notes = "sample for '%s', uploaded %s" % (fname, now)
            sample_kws = {}
            for attr in ('preparation', 'formula'):
                shortname = attr[:4]
                if shortname in sample_attrs:
                    sample_kws[attr] = sample_attrs.pop(shortname)
                elif attr in sample_attrs:
                    sample_kws[attr] = sample_attrs.pop(attr)

            if len(sample_attrs) > 0:
                sample_notes = '%s\n%s' % (sample_notes, json_encode(sample_attrs))
            if reuse_sample:
                srow = self.lookup('sample', name=sample_name, person_id=person_id)
                if len(srow) > 0:
                    sample_id = srow[0].id
            if sample_id == 0:
                sample_id = self.add_sample(sample_name, person_id,
                                            notes=sample_notes, **sample_kws)
        self.session.commit()
        time.sleep(0.025)
        if reference_mode != 'none':
            if reference_sample is None:
                reference_sample = 'unknown'
        else:
            reference_sample = 'none'
        beamline_name  = xfile.attrs['beamline']['name']
        notes = json_encode(xfile.attrs)
        if verbose:
            print(f"adding {fname}: {element} {edge}, '{mode}' {len(energy):d} points")

        return self.add_spectrum(spectrum_name, description=description,
                                 d_spacing=d_spacing, collection_date=c_date,
                                 person=person_id, beamline=beamline_name,
                                 edge=edge, element=element, mode=mode,
                                 energy=energy, energy_units=en_units,
                                 i0=i0, itrans=itrans, ifluor=ifluor,
                                 irefer=irefer, sample=sample_id,
                                 comments=comments, notes=notes,
                                 filetext=filetext,
                                 reference_sample=reference_sample,
                                 reference_mode=reference_mode,
                                 temperature=temperature,
                                 commit=commit)



def connect_xaslib(dbname, server='sqlite', user='', password='',
                   port=5432, host=''):
    """connect to a XAS Data Library"""
    return XASDataLibrary(dbname,
                          server=server, user=user,
                          password=password, port=port, host=host)

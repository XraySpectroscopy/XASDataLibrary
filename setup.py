#!/usr/bin/env python
from setuptools import setup
import os

version = '0.1'
with open(os.path.join('xasdb', '_version.py')) as fh:
    for line in fh.readlines():
        line = line[:-1].strip()
        if line.startswith('__version'):
            words = line.split('=') + [' ', ' ']
            version = words[1].strip().replace("'", '').replace('"', '')

#

setup(name = 'xasdb',
      version = version,
      author = 'Matthew Newville',
      author_email = 'newville@cars.uchicago.edu',
      url     = 'http://xas.org/XasDataLibrary',
      license = 'Public Domain',
      description = 'x-ray absorption spectra library',
      install_requires=('sqlalchemy', 'numpy', 'scipy'),
      package_dir = {'xasdb': 'xasdb'},
      packages = ['xasdb','xasdb.wx']
)

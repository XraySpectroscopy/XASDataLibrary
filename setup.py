#!/usr/bin/env python
from setuptools import setup
import os

version = '0.3'
with open(os.path.join('xaslib', '_version.py')) as fh:
    for line in fh.readlines():
        line = line[:-1].strip()
        if line.startswith('__version'):
            words = line.split('=') + [' ', ' ']
            version = words[1].strip().replace("'", '').replace('"', '')


pkg_data = {'xaslib.template': ['template/*', 'templates/doc/*'],
            'xaslib.static': ['static/*']}


setup(name='xaslib',
      version = version,
      author       = 'Matthew Newville',
      author_email = 'newville@cars.uchicago.edu',
      url          = 'https://xrayabsorption.org/xaslib',
      license      = 'Public Domain',
      description  = 'X-ray Absorption Spectra Data Library',
      install_requires=('sqlalchemy', 'numpy', 'scipy', 'xraydb'),
      package_dir = {'xaslib': 'xaslib'},
      package_data = pkg_data,
      packages = ['xaslib'],
)

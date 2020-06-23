# -*- coding: utf-8 -*-
#

# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join('.', 'ext')))

project = 'X-ray Absorption Data Library'
copyright = 'Public Domain.'
release = '0.1'
html_title  = 'X-ray Absorption Data Library'
html_short_title = 'xaslib.xrayabsorption.org'

pygments_style = 'sphinx'
html_theme = 'classic'
html_theme = 'pyramid'

extensions = ['sphinx.ext.mathjax']

templates_path = ['_templates']
source_suffix = '.rst'
source_encoding = 'utf-8'

master_doc = 'index'

exclude_trees = ['_build']

add_function_parentheses = True
add_module_names = False

html_static_path = ['_static']
html_favicon = '_static/ixas_logo.ico'

rst_prolog = """
.. include:: <s5defs.txt>
"""

language = None

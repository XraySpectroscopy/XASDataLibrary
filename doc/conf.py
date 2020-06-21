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
# html_sidebars = {'index': ['globaltoc.html','searchbox.html']}

language = None
# html_theme_options = {
#     "rightsidebar": "false",
#     "relbarbgcolor": "#16C",
#     "relbartextcolor": "#FEA",
#     "sidebarbgcolor": "#F2F2F2",
#     "sidebarbtncolor": "#16C",
#     "sidebartextcolor": "#16C",
#     "sidebarlinkcolor": "#16C",
#     "footerbgcolor": "#EEE",
#     "footertextcolor": "#000",
# }

"""
footerbgcolor (CSS color): Background color for the footer line.
footertextcolor (CSS color): Text color for the footer line.
sidebarbgcolor (CSS color): Background color for the sidebar.
sidebarbtncolor (CSS color): Background color for the sidebar collapse button (used when collapsiblesidebar is true).
sidebartextcolor (CSS color): Text color for the sidebar.
sidebarlinkcolor (CSS color): Link color for the sidebar.
relbarbgcolor (CSS color): Background color for the relation bar.
relbartextcolor (CSS color): Text color for the relation bar.
relbarlinkcolor (CSS color): Link color for the relation bar.
bgcolor (CSS color): Body background color.
textcolor (CSS color): Body text color.
linkcolor (CSS color): Body link color.
visitedlinkcolor (CSS color): Body color for visited links.
headbgcolor (CSS color): Background color for headings.
headtextcolor (CSS color): Text color for headings.
headlinkcolor (CSS color): Link color for headings.
codebgcolor (CSS color): Background color for code blocks.
codetextcolor (CSS color): Default text color for code blocks, if not set differently by the highlighting style.
bodyfont (CSS font-family): Font for normal text.
headfont
"""

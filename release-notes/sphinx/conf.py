# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import datetime

project = 'Release Notes'
copyright = u'1988, ' + \
    str(datetime.datetime.now().year) + \
    ' RTEMS Project and contributors'
author = 'RTEMS Project and contributors'
release = '1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_inline_tabs',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = []

myst_enable_extensions = [
    "deflist",
    "attrs_block"
]

pygments_style = 'sphinx'

html_copy_source = False
html_show_sourcelink = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
html_css_files = [
    'rrn-styles.css',
]

# -- Options for LaTeX output --------------------------------------------------
latex_engine = 'pdflatex'
latex_use_xindy = False
latex_paper_size = 'a4'
latex_show_pagerefs = True
latex_use_modindex = False
latex_additional_files = ['rtemsstyle.sty', 'rtemsextrafonts.sty', 'logo.pdf']

# Additional stuff for LaTeX
#    'fontpkg':      r'\usepackage{mathpazo}',
latex_elements = {
    'papersize':    'a4paper',
    'pointsize':    '11pt',
    'releasename':  '',
    'preamble':     r'''
\newcommand{\rtemscopyright}{%s}
\usepackage{rtemsstyle}
''' % (copyright),
    'maketitle': r'\rtemsmaketitle',
    'parsedliteralwraps': True,
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
try:
    import os
    import sys
    sys.path += [os.getcwd()]
    import rnlatex
    latex_documents = rnlatex.latex_documents
except:
    latex_documents = []

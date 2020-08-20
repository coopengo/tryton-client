#!/usr/bin/env python3
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from setuptools import setup, find_packages
import io
import os
import re


def read(fname):
    return io.open(
        os.path.join(os.path.dirname(__file__), fname),
        'r', encoding='utf-8').read()


args = {}
try:
    from babel.messages import frontend as babel

    class extract_messages(babel.extract_messages):
        def initialize_options(self):
            super().initialize_options()
            self.omit_header = True
            self.no_location = True

    class update_catalog(babel.update_catalog):
        def initialize_options(self):
            super().initialize_options()
            self.omit_header = True
            self.ignore_obsolete = True

    args['cmdclass'] = {
        'compile_catalog': babel.compile_catalog,
        'extract_messages': extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': update_catalog,
        }

    args['message_extractors'] = {
        'tryton': [
            ('**.py', 'python', None),
            ],
        }

except ImportError:
    pass

package_data = {
    'tryton': ['data/pixmaps/tryton/*.png',
        'data/pixmaps/tryton/*.svg',
        'data/locale/*/LC_MESSAGES/*.mo',
        'data/locale/*/LC_MESSAGES/*.po',
        ]
    }
data_files = []


def get_version():
    init = read(os.path.join('tryton', '__init__.py'))
    return re.search('__version_coog__ = "([0-9.]*)"', init).group(1)


name = 'Coog'

version = get_version()

dist = setup(name=name,
    version=version,
    description='Coog client',
    long_description=read('README'),
    author='Coopengo',
    author_email='support@coopengo.com',
    url='http://www.coopengo.com',
    keywords='Insurance ERP',
    packages=find_packages(),
    package_data=package_data,
    data_files=data_files,
    scripts=['bin/tryton'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: GTK',
        'Framework :: Tryton',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: Bulgarian',
        'Natural Language :: Catalan',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: Czech',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: Finnish',
        'Natural Language :: French',
        'Natural Language :: German',
        'Natural Language :: Hungarian',
        'Natural Language :: Indonesian',
        'Natural Language :: Italian',
        'Natural Language :: Persian',
        'Natural Language :: Polish',
        'Natural Language :: Portuguese (Brazilian)',
        'Natural Language :: Russian',
        'Natural Language :: Slovenian',
        'Natural Language :: Spanish',
        'Natural Language :: Turkish',
        'Natural Language :: Japanese',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Office/Business',
        ],
    platforms='any',
    license='GPL-3',
    python_requires='>=3.5',
    install_requires=[
        'pycairo',
        "python-dateutil",
        'PyGObject',
        ],
    extras_require={
        'calendar': ['GooCalendar>=0.7'],
        },
    zip_safe=False,
    test_suite='tryton.tests',
    **args
    )

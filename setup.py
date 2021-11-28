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

    args['cmdclass'] = {
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog,
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
    return re.search('__version__ = "([0-9.]*)"', init).group(1)


version = get_version()
major_version, minor_version, _ = version.split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)
name = 'tryton'

download_url = 'http://downloads.tryton.org/%s.%s/' % (
    major_version, minor_version)
if minor_version % 2:
    version = '%s.%s.dev0' % (major_version, minor_version)
    download_url = 'hg+http://hg.tryton.org/%s#egg=%s-%s' % (
        name, name, version)

dist = setup(name=name,
    version=version,
    description='Tryton client',
    long_description=read('README'),
    author='Tryton',
    author_email='issue_tracker@tryton.org',
    url='http://www.tryton.org/',
    download_url=download_url,
    keywords='business application ERP',
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
        'Natural Language :: French',
        'Natural Language :: German',
        'Natural Language :: Hungarian',
        'Natural Language :: Italian',
        'Natural Language :: Persian',
        'Natural Language :: Polish',
        'Natural Language :: Portuguese (Brazilian)',
        'Natural Language :: Russian',
        'Natural Language :: Slovenian',
        'Natural Language :: Spanish',
        'Natural Language :: Japanese',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business',
        ],
    platforms='any',
    license='GPL-3',
    python_requires='>=3.4',
    install_requires=[
        'pycairo',
        "python-dateutil",
        'PyGObject>=3.19',
        ],
    extras_require={
        'calendar': ['GooCalendar>=0.4'],
        },
    zip_safe=False,
    **args
    )

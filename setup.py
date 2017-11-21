#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

here = lambda *a: os.path.join(os.path.dirname(__file__), *a)
version='0.1.0b2'

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open(here('README.md')).read()
history = open(here('HISTORY.rst')).read().replace('.. :changelog:', '')
requirements = [x.strip() for x in open(here('requirements.txt')).readlines()]

setup(
    name='aioouimeaux',
    version=version,
    description='Open source control for Belkin WeMo devices',
    long_description=readme + '\n\n' + history,
    author='François Wautier',
    author_email='francois@wautier.eu',
    url='https://github.com/frawau/aioouimeaux',
    download_url='https://github.com/frawau/aioouimeaux/archive/'+version+'.tar.gz',
    packages=find_packages(),
    #packages=[
        #'aioouimeaux',packages=find_packages()
    #],
    package_dir={'aioouimeaux': 'aioouimeaux'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    python_requires='>=3.6',
    keywords='aioouimeaux WeMo automation',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Home Automation',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',

        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
)

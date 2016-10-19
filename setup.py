from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import io
import os
import re

from functools import partial

from setuptools import setup, find_packages


get_path = partial(os.path.join,  os.path.dirname(os.path.abspath(__file__)))


def get_version(path):
    version = None
    try:
        version = \
            re.search(r'__version__\s*=\s*[\'"]([\d.]+)[\'"]',
                      io.open(path, encoding='utf-8').read()).group(1)
    except (IOError, AttributeError):
        pass
    return version


setup(name='splitfile',
      author='Greg Banks',
      author_email='quaid@kuatowares.com',
      version=get_version(get_path('splitfile/_version.py')),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Utility',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
      ],
      keywords='AWS S3 boto multipart upload split',
      url='https://github.com/gregbanks/splitfile',
      description='Treat a file as an ordered set of smaller files',
      long_description=io.open(get_path('README.rst'), encoding='utf-8').read(),
      packages=find_packages(exclude=('tests',)),
      test_suite='nose2.collector.collector',
      install_requires=[
          'six'
      ],
      extras_require={
          'dev': [
              'ipdb'
          ],
          'test': [
              'nose2',
              'cov-core',
              'tox',
              'pylint',
              'boto',
              'boto3'
          ]
      })

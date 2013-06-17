import os
import re

from functools import partial

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages


# NOTE: http://bugs.python.org/issue15881#msg170215
try:
        import multiprocessing
except ImportError:
        pass


get_path = partial(os.path.join,  os.path.dirname(os.path.abspath(__file__)))


setup(name='splitfile',
      author='Greg Banks',
      author_email='quaid@kuatowares.com',
      description='allows one to iterate over the contents of a file in '
                  'chunks, where each of those chunks is a file like object '
                  'itself.',
      setup_requires=['rexparse'],
      dependency_links=['https://github.com/gregbanks/rexparse/archive/master.zip#egg=rexparse'],
      rexparse={'requirements_path': get_path('requirements.txt'),
                'version_path': get_path('splitfile', '_version.py')},
      test_suite='nose.collector',
      packages=['splitfile'])


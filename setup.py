import os
import re

from setuptools import setup

setup_dir = os.path.dirname(__file__)

def version():
    version_path = os.path.join(setup_dir, 'splitfile', '_version.py')
    try:
        return re.search(r'__version__\s*=\s*[\'"]([\d.]+)[\'"]', 
                         open(version_path).read()).group(1)
    except (IOError, AttributeError):
        pass
    return None

def requirements():
    inst_reqs = []
    test_reqs = []
    reqs      = inst_reqs
    for line in open(os.path.join(setup_dir, 'requirements.txt')):
        line = line.strip()
        if len(line) == 0:
            continue
        elif line.startswith('#'):
            if 'install' in line.lower():
                reqs = inst_reqs
            elif 'test' in line.lower():
                reqs = test_reqs
            continue
        reqs.append(line)
    return {'install': inst_reqs, 'test': test_reqs}

setup(name='splitfile',
      version=version(),
      author='Greg Banks',
      author_email='quaid@kuatowares.com',
      description='allows one to iterate over the contents of a file in '
                  'chunks where each of those chunks is a file like object '
                  'itself',
      install_requires=requirements()['install'],
      tests_require=requirements()['test'],
      test_suite='splitfile.tests')


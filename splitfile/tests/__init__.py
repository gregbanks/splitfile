import os
import shutil

from tempfile import mkstemp
from unittest import TestCase

from splitfile import SplitFile


data_path = os.path.join(os.path.dirname(__file__), 'data', 'test.bin')


class BaseTest(TestCase):
    chunk_size = 1024

    def setUp(self):
        fd, temp_path = mkstemp()
        shutil.copyfileobj(open(data_path), os.fdopen(fd, 'w'))
        self._split_file = SplitFile(temp_path, self.__class__.chunk_size)

    def tearDown(self):
        self._split_file.close()
        os.unlink(self._split_file.file.name)


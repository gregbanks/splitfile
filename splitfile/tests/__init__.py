from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import io
import logging
import os
import shutil

from tempfile import mkstemp
from unittest import TestCase

from splitfile import SplitFile


data_path = os.path.join(os.path.dirname(__file__), 'data')

logging.basicConfig(level=logging.CRITICAL)


class BaseTest(TestCase):
    chunk_size = 1024

    def setUp(self):
        bin_fd = None
        try:
            bin_fd, bin_temp_path = mkstemp()
            shutil.copyfileobj(
                io.open(os.path.join(data_path, 'test.bin'), 'rb'),
                io.open(bin_fd, 'wb', closefd=False))
            self._bin_split_file = \
                SplitFile(bin_temp_path, self.__class__.chunk_size)
        finally:
            if bin_fd is not None:
                os.close(bin_fd)
        self.split_file = self._bin_split_file

    def tearDown(self):
        self._bin_split_file.close()
        os.unlink(self._bin_split_file.file.name)


import hashlib
import math
import os

from StringIO import StringIO
from unittest import SkipTest

from . import BaseTest


class SplitFileTest(BaseTest):
    # iterator tests
    def test_iterator(self):
        num_chunks = math.ceil((1.0 * self._split_file.size) /
                               self.__class__.chunk_size)
        self.assertEqual(num_chunks, sum([1 for _ in self._split_file]))

    def test_data_integrity(self):
        data = StringIO()
        for chunk in self._split_file:
            data.write(chunk.read())
        split_file_hash = hashlib.md5()
        split_file_hash.update(data.getvalue())

        file_hash = hashlib.md5()
        self._split_file.file.seek(0)
        file_hash.update(self._split_file.file.read())

        self.assertEqual(file_hash.digest(), split_file_hash.digest())

    # sequence tests
    def test_len(self):
        num_chunks = math.ceil((1.0 * self._split_file.size) /
                               self.__class__.chunk_size)
        self.assertEqual(num_chunks, len(self._split_file))

    def test_getitem(self):
        iter_list = [c.read() for c in self._split_file]
        getitem_list = [self._split_file[i].read()
                        for i in xrange(len(self._split_file))]
        self.assertListEqual(iter_list, getitem_list)

        iter_list.reverse()
        getitem_list = [self._split_file[i].read()
                        for i in xrange(-1,
                                        -1 * (len(self._split_file) + 1),
                                        -1)]
        self.assertListEqual(iter_list, getitem_list)

    # delete range tests
    def test_delete_range(self):
        raise SkipTest('not yet implemented')

    # move range tests
    def test_move_range(self):
        raise SkipTest('not yet implemented')

    # bytes remaining tests
    def test_bytes_remaining(self):
        count = 0
        for _ in self._split_file:
            self.assertEqual(self._split_file.size -
                             (count * self._split_file.chunk_size),
                             self._split_file.bytes_remaining)
            count += 1


class ChunkTest(BaseTest):
    # read test
    def test_read(self):
        for chunk in self._split_file:
            data = self._split_file.read(10)
            chunk.seek(0)
            self.assertEqual(data, chunk.read(10))

    def test_read_past_end(self):
        chunk = self._split_file[0]
        chunk.read(self._split_file.chunk_size)
        self.assertEqual('', chunk.read())

    def test_read_all(self):
        chunk = self._split_file[0]
        self.assertEqual(self._split_file.chunk_size, len(chunk.read()))

    # bytes remaining tests

    # seek tests
    def test_seek_in_bounds(self):
        chunk = self._split_file[0]
        chunk.seek(chunk.size / 2)
        self.assertEqual(chunk.size / 2, self._split_file.tell())

        chunk.seek(chunk.size / 4, os.SEEK_CUR)
        self.assertEqual((3 * chunk.size) / 4, self._split_file.tell())

        chunk.seek(chunk.size / -2, os.SEEK_END)
        self.assertEqual(chunk.size / 2, self._split_file.tell())

    def test_seek_before_start(self):
        chunk = self._split_file[1]
        self.assertRaises(IOError, chunk.seek, -1)
        self.assertRaises(IOError, chunk.seek, -1, os.SEEK_CUR)
        self.assertRaises(IOError, chunk.seek, -1 * chunk.size - 1, os.SEEK_END)

    def test_seek_after_end(self):
        chunk = self._split_file[1]
        chunk.seek(chunk.size * 2)
        self.assertEqual(chunk.size, chunk.tell())
        chunk.seek(chunk.size * 2, os.SEEK_CUR)
        self.assertEqual(chunk.size, chunk.tell())
        chunk.seek(chunk.size * 2, os.SEEK_END)
        self.assertEqual(chunk.size, chunk.tell())

    # tell tests
    def test_tell(self):
        chunk = self._split_file[1]
        self.assertEqual(0, chunk.tell())
        self.assertEqual(self._split_file.chunk_size, self._split_file.tell())
        chunk.read(10)
        self.assertEqual(10, chunk.tell())
        self.assertEqual(self._split_file.chunk_size + 10,
                         self._split_file.tell())

    # write tests
    def test_write_within_chunk(self):
        raise SkipTest('not yet implemented')

    def test_write_past_end(self):
        raise SkipTest('not yet implemented')

    # truncate tests
    def test_truncate_intermediate_chunk(self):
        raise SkipTest('not yet implemented')


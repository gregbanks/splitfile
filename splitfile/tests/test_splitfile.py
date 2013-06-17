import hashlib
import math
import os
import random
import re
import shutil
import string
import sys

from StringIO import StringIO
from tempfile import mkstemp
from unittest import SkipTest, TestCase

try:
    import boto
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from boto.s3.exceptions import S3ResponseError
    from boto.s3.multipart import MultiPartUpload
except ImportError:
    pass

from . import BaseTest, data_path
from splitfile import SplitFile


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

    def test_contains(self):
        chunk = self._split_file[2]
        self.assertTrue(chunk in self._split_file)
        other_file = SplitFile(os.path.join(data_path, 'test2.bin'),
                               self.__class__.chunk_size)
        self.assertFalse(other_file[2] in self._split_file)


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


class BotoTest(BaseTest):
    def setUp(self):
        super(BotoTest, self).setUp()
        if 'boto' not in globals():
            raise SkipTest('boto pkg not found')
        env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
                    'SPLITFILE_TEST_BUCKET', 'SPLITFILE_LARGE_TEST_FILE']
        if not all([v in os.environ for v in env_vars]):
            raise SkipTest('the following environment variables must be set '
                           'to run boto tests: %r' % (env_vars))

        fd, temp_path = mkstemp()
        shutil.copyfileobj(open(os.environ['SPLITFILE_LARGE_TEST_FILE']),
                           os.fdopen(fd, 'w'))
        self._split_file = SplitFile(temp_path, 6 * 2**20)

        self.con = S3Connection()
        self.bucket = self.con.create_bucket(os.environ['SPLITFILE_TEST_BUCKET'])
        self.key_name = [random.choice(string.ascii_letters) for _ in xrange(16)]

    def tearDown(self):
        super(BotoTest, self).tearDown()
        for k in self.bucket.list():
            k.delete()
        self.bucket.delete()

    def test_multipart_upload(self):
        upload = self.bucket.initiate_multipart_upload(self.key_name)
        for i, chunk in enumerate(self._split_file):
            upload.upload_part_from_file(chunk, i + 1)
        upload.complete_upload()
        fd, temp_path = mkstemp()
        try:
            with open(temp_path, 'w+') as download:
                self.bucket.get_key(
                    self.key_name).get_contents_to_file(download)
                sf_hash = hashlib.md5()
                for c in self._split_file:
                    sf_hash.update(c.read())
                download.seek(0)
                dl_hash = hashlib.md5()
                while True:
                    data = download.read(2**20)
                    if not data:
                        break
                    dl_hash.update(data)
            self.assertEqual(dl_hash.digest(), sf_hash.digest())
        finally:
            os.unlink(temp_path)


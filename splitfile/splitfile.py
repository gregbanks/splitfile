from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

import io
import logging
import os
import stat

from collections import Sequence

import six

from .chunk import Chunk


logger = logging.getLogger(__name__)


class SplitFile(Sequence):
    """SplitFile class

    Open a file and allow for iteration of file chunks where each chunk can be
    treated as an individual file.

    XXX: only binary mode supported at the moment
    """
    def __init__(self, file_, chunk_size=2**20, mode='rb', encoding=None,
                       errors=None, newline=None, closefd=False):
        """Constructor

        :param file_: the file to split
        :type file_: str, file, io.IOBase

        .. note:: If we are on python 2.7 and `file_` is a `file` object, we
            we will dup the fd and open that with `io.open` internally. In this
            case, `mode`, `encoding`, and `errors` will be inherited from the
            file object passed to the constructor. `newline` and `closefd` will
            *not* be inherited, but will be sourced from the parameters passed
            to the constructor.
        """
        self._file = file_

        # check mode passed in is valid (update with 'b' flag if necessary)
        if six.PY2 and len(mode) >= 1:
            if len(mode) == 1 or mode[1] != 'b':
                logger.warning('adding binary flag to mode...')
                mode = mode[0] + 'b' + mode[1:]
        if not mode.startswith('rb'):
            raise ValueError('mode must be "rb\\+?"')

        # if it looks like we got passed a path, make sure it's a valid file
        # and open it
        if isinstance(self._file, six.string_types):
            if not os.path.isfile(self._file):
                raise ValueError('{} is not a regular file'.format(self._file))
            self._file = io.open(self._file, mode=mode, encoding=encoding,
                                 errors=errors, newline=newline,
                                 closefd=True)

        # if we're on python 2.x, convert to io.IOBase
        if six.PY2 and isinstance(self._file, file):
            self._file = io.open(self._file.fileno(), mode,
                                 self._file.encoding, self._file.errors,
                                 newline, closefd)

        # make sure we've got a file after all that
        if not isinstance(self._file, io.IOBase):
            raise ValueError('file_ must be a path or an actual file')

        # make sure the file we've got has an appropriate mode
        if not self._file.mode.startswith('rb'):
            raise ValueError('mode must be "rb" or "rb+"')

        # make sure it's a file of the appropriate type
        if not (self.is_reg or self.is_fifo):
            raise ValueError('file type must be S_IFREG or S_IFIFO')

        self._chunk_size = chunk_size
        self._iterating = False
        self._current_offset = 0
        self._cur_chunk = None
        self._file.seek(0)

    proxied_attrs = [
        'close',
        'closed',
        'encoding',
        'errors',
        'fileno',
        'flush',
        'isatty',
        'mode',
        'name',
        'newlines',
        'read',
        'readline',
        'readlines',
        'seek',
        'seekable',
        'tell',
        'truncate',
        'write',
        'writelines'
        'xreadlines',
    ]

    def __getattr__(self, attr):
        if attr in self.__class__.proxied_attrs:
            return getattr(self._file, attr)
        raise AttributeError(attr)

    def __iter__(self):
        if self._cur_chunk is not None:
            self._cur_chunk.close()
        self._iterating = True
        self._current_offset = None
        self._cur_chunk = None
        self.seek(0)
        return self

    def __next__(self):
        if not self._iterating:
            raise RuntimeError('invalid iterator')

        if self._current_offset is None:
            self._current_offset = 0
        else:
            self._cur_chunk.seek(0, os.SEEK_END)
            self._current_offset = self._file.tell()
            self._cur_chunk.close()
        if self._current_offset >= self.size:
            self._iterating = False
            self._current_offset = None
            self._cur_chunk = None
            raise StopIteration()
        self._cur_chunk = Chunk(self)
        return self._cur_chunk

    def next(self):
        return self.__next__()

    def __getitem__(self, index):
        self._iterating = False
        index = len(self) + index if index < 0 else index
        if index < 0 or index >= len(self):
            raise IndexError('index out of range')
        self._current_offset = index * self._chunk_size
        self.seek(self._current_offset)
        self._cur_chunk = Chunk(self)
        return self._cur_chunk

    def __len__(self):
        return self.size // self._chunk_size + \
                (1 if self.size % self._chunk_size != 0 else 0)

    def __contains__(self, item):
        logging.warning('__contains__ is very inefficient')
        item_md5 = item.md5
        for chunk in self:
            if chunk.md5 == item_md5:
                return True
        return False

    @property
    def is_reg(self):
        return stat.S_ISREG(os.fstat(self._file.fileno()).st_mode)

    @property
    def is_fifo(self):
        return stat.S_ISFIFO(os.fstat(self._file.fileno()).st_mode)

    @property
    def size(self):
        return os.fstat(self._file.fileno()).st_size

    @property
    def chunk(self):
        return self._cur_chunk

    @property
    def iterating(self):
        return self._iterating

    @property
    def bytes_remaining(self):
        return self.size - self._file.tell()

    @property
    def offset(self):
        return self._current_offset

    @property
    def chunk_size(self):
        return self._chunk_size

    @property
    def file(self):
        return self._file

    def delete_range(self, offset, length):
        raise NotImplementedError()

    def move_range(self, src_offset, length, dst_offset):
        raise NotImplementedError()



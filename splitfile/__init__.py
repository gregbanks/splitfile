import os

from collections import Sequence

from .chunk import Chunk
from _version import __version__


class SplitFile(Sequence):
    def __init__(self, file_, chunk_size=2**20):
        self._file = file_
        if isinstance(file_, basestring):
            if not os.path.isfile(file_):
                raise ValueError('%s is not a regular file' % (file_))
            self._file = open(file_, 'r+')
        if not isinstance(self._file, file):
            raise ValueError('file_ must be a path or an actual file')
        if not self._file.mode.startswith('r'):
            raise ValueError('file_ must be opened with mode "r" or "r+"')
        self._chunk_size = chunk_size

        self._iterating = False
        self._current_offset = 0
        self._cur_chunk = None

        self._file.seek(0)

    proxied_attrs = ['close', 'fileno', 'flush', 'isatty', 'closed', 'encoding',
                     'errors', 'mode', 'name', 'newlines', 'softspace', 'read',
                     'readline', 'readlines', 'xreadlines', 'seek', 'tell',
                     'truncate', 'write', 'writelines']

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

    def next(self):
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
                1 if self.size % self._chunk_size != 0 else 0

    def __contains__(self, item):
        pos = item.tell()
        try:
            item.seek(0)
            data = item.read()
            for chunk in self:
                if data == chunk.read():
                    return True
        finally:
            item.seek(pos)
        return False

    @property
    def size(self):
        return os.stat(self._file.name).st_size

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


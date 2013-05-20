import os

from functools import wraps


class Chunk(object):
    def __init__(self, container):
        self._container = container
        self._size = min(container.chunk_size, container.bytes_remaining)
        self._offset = container.offset
        self._closed = False
        self.seek(0)

    def __check_open(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.closed:
                raise ValueError('I/O operation on closed file')
            return func(self, *args, **kwargs)
        return wrapper

    @__check_open
    def __getattr__(self, attr):
        return getattr(self._container, attr)

    @__check_open
    def __iter__(self):
        self.seek(0)
        return self

    @property
    @__check_open
    def size(self):
        return self._size

    @property
    @__check_open
    def bytes_remaining(self):
        return self._size - self.tell()

    @property
    def closed(self):
        return self._container.closed or self._closed

    def close(self):
        self._closed = True

    @__check_open
    def next(self):
        pos = self.tell()
        if pos < self._size:
            line = self._container.file.readline(self.bytes_remaining)
            if line != '':
                return line
        raise StopIteration()

    @__check_open
    def read(self, size=-1):
        size = self.bytes_remaining if size < 0 else size
        return self._container.file.read(min(size, self.bytes_remaining))

    @__check_open
    def readline(self, size=-1):
        size = self.bytes_remaining if size < 0 else size
        return self._container.file.readline(min(size, self.bytes_remaining))

    @__check_open
    def readlines(self, sizehint=-1):
        bytes_remaining = self.bytes_remaining
        lines = self._container.file.readlines(bytes_remaining)
        index = 0
        data_len = sum([len(l) for l in lines])
        while data_len > bytes_remaining:
            index -= 1
            data_len -= len(lines[index])
        return lines[:index] + [lines[index][:bytes_remaining - data_len]]

    @__check_open
    def xreadlines(self):
        return iter(self)

    @__check_open
    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            if offset < 0:
                raise IOError('invalid argument')
            self._container.file.seek(self._offset + min(offset, self._size),
                                      whence)
        elif whence == os.SEEK_CUR:
            pos = self.tell()
            if pos + offset < 0:
                raise IOError('invalid argument')
            self._container.file.seek(min(offset, self._size - pos),
                                      whence)
        elif whence == os.SEEK_END:
            if self._size + offset < 0:
                raise IOError('invalid argument')
            if offset >= 0:
                self._container.file.seek(self._offset + self._size)
            else:
                self._container.file.seek(self._offset + self._size + offset)
        else:
            raise ValueError('unknown value for whence %s' % (str(whence)))

    @__check_open
    def tell(self):
        return self._container.file.tell() - self._container.offset

    @__check_open
    def truncate(self, size=None):
        raise NotImplementedError()

    @__check_open
    def write(self, str_):
        raise NotImplementedError()

    @__check_open
    def writelines(self, sequence):
        raise NotImplementedError()


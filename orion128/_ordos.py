#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.


class ORDOSFile:
    '''An ORDOS file: a name, a load address and the data.

    On a disk the file is stored as a record: a 16-byte header, then the
    data. The header holds the name padded with spaces to 8 bytes, the
    2-byte load address, the 2-byte data size and four unused bytes. A
    host file is a copy of such a record, often followed by padding from
    the sector or block it was cut out of.
    '''
    HEADER_SIZE = 16
    NAME_SIZE = 8

    def __init__(self, name: bytes, load_addr: int, data: bytes) -> None:
        if len(name) > self.NAME_SIZE:
            raise ValueError(f'ORDOS file name {name!r} is longer than '
                             f'{self.NAME_SIZE} bytes')
        if len(data) > 0xffff:
            raise ValueError(f'ORDOS file data of {len(data)} bytes does '
                             f'not fit the 2-byte size field')
        self.name = name
        self.load_addr = load_addr
        self.data = data

    @classmethod
    def parse(cls, image: bytes) -> 'ORDOSFile':
        '''Read the file out of a stored record.

        Anything after the data is padding and is dropped. Raises
        ValueError if the image is too short for the record it describes.
        '''
        if len(image) < cls.HEADER_SIZE:
            raise ValueError(f'shorter than the {cls.HEADER_SIZE}-byte '
                             f'ORDOS file header')
        name = image[:cls.NAME_SIZE].rstrip(b' ')
        load_addr = int.from_bytes(image[8:10], 'little')
        size = int.from_bytes(image[10:12], 'little')
        data = image[cls.HEADER_SIZE:cls.HEADER_SIZE + size]
        if len(data) < size:
            raise ValueError(f'the ORDOS header says {size} bytes of '
                             f'data, but the file has only {len(data)}')
        return cls(name, load_addr, data)

    def to_record(self) -> bytes:
        '''Assemble the record that stores the file on a disk.'''
        return (self.name.ljust(self.NAME_SIZE)
                + self.load_addr.to_bytes(2, 'little')
                + len(self.data).to_bytes(2, 'little')
                + bytes(4)
                + self.data)

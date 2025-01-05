from display_drivers import DisplayDriver
import sys
import os

class Bmp(DisplayDriver):
    def __init__(self, filename, width, height) -> None:
        self._filename = filename
        self._width = width
        self._height = height

        self._header = bytearray(b'\x42\x4d')
        # BMP header
        self._header += ((width * height)+62).to_bytes(4, sys.byteorder)
        self._header += b'\x00\x00' # reserved
        self._header += b'\x00\x00' # reserved
        self._header += (62).to_bytes(4, sys.byteorder) # offset

        # DIP header
        self._header += (40).to_bytes(4, sys.byteorder) # DIP header size
        self._header += (width).to_bytes(4, sys.byteorder) # image width
        self._header += (height).to_bytes(4, sys.byteorder) # image height
        self._header += (1).to_bytes(2, sys.byteorder) # number of color plane
        self._header += (8).to_bytes(2, sys.byteorder) # number of bits per pixel
        self._header += b'\x00\x00\x00\x00' # compression (0 = no compression)
        self._header += (width * height).to_bytes(4, sys.byteorder) # image size
        self._header += (65536).to_bytes(4, sys.byteorder) # horizontal res
        self._header += (65536).to_bytes(4, sys.byteorder) # vertical res
        self._header += (2).to_bytes(4, sys.byteorder) # number of colors (0 = 2^32)
        self._header += (2).to_bytes(4, sys.byteorder) # number of important colors (0 = 2^32)

        # Color table
        self._header += b'\x00\x00\x00\x00' # black
        self._header += b'\xff\xff\xff\x00' # white

    async def init(self) -> None:
        pass

    async def print_buffer(self, buffer: bytearray) -> None:
        f = open('{}-tmp'.format(self._filename), 'w')
        self._add_header(f)

        for i in range(0, self._height):
            # Buffer 0,0 is upper left corner while it is lower left in BMP
            height = (self._height - i) - 1
            row = height // 8
            bit = height % 8
            for j in range(0, self._width):
                index = (row * self._width) + j
                val = ((buffer[index] >> bit) & 0x01).to_bytes(1)
                f.write(val)
        f.close()
        os.rename('{}-tmp'.format(self._filename), '{}'.format(self._filename))

    def _add_header(self, f) -> None:
        f.write(self._header)


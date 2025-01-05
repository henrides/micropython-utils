import machine
import sys

# leading zeros | start bit | SGL/DIFF bit | ODD/SIGN bit | MBSF bit
CHANNEL_0 = b'\x0d' # start = 1, SGL = 1, ODD = 0, MBSF = 1
CHANNEL_1 = b'\x0f' # start = 1, SGL = 1, ODD = 1, MBSF = 1
CHANNEL_DIFF_PLUS = b'\x09' # start = 1, SGL = 0, ODD = 0, MBSF = 1
CHANNEL_DIFF_MINUS = b'\x0b' # start = 1, SGL = 0, ODD = 1, MBSF = 1

class Mcp3xxx():
    def __init__(self, spi: machine.SPI, cs: machine.Pin, channel=CHANNEL_0, bits=10, ref=5):
        self._spi = spi
        self._cs = cs
        self._channel = channel
        self._bits = bits
        self._ref = ref
        self._rxdata = bytearray(2)
        self._txdata = (int.from_bytes(channel, sys.byteorder) << (bits - 7)).to_bytes(2, sys.byteorder)

        self._cs(1)
        pass

    def read_u16(self):
        try:
            self._cs(0)
            self._spi.write_readinto(self._txdata, self._rxdata)
        finally:
            self._cs(1)

        #self._rxdata = b'\x00\x7e'
        #print(''.join('{:02x}'.format(x) for x in self._rxdata))
        return int.from_bytes(self._rxdata, 'big') # MBSF bit means big endian

    def read_uv(self):
        return (self.read_u16() * self._ref) / (1 << self._bits) * 1_000_000


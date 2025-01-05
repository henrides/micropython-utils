import machine

CHANNEL_0 = 0
CHANNEL_1 = 1

GAIN_1 = 1
GAIN_2 = 0

class Mcp48x2():
    def __init__(self, spi: machine.SPI, cs: machine.Pin, channel=CHANNEL_0, ref=2.048, gain=GAIN_1):
        self._spi = spi
        self._cs = cs
        self._channel = channel
        self._ref = ref
        self._gain = 1 if gain == GAIN_1 else 0

        self._txdata = bytearray(2)
        self._set_txdata()

        self._cs(1)

    def _set_txdata(self):
        # Channel bit | dont care bit | gain bit | output shutdown bit
        self._txdata[0] = (((self._channel << 7) & 0x80) | ((self._gain << 5) & 0x20) | 0x10) & 0xf0

    def write_u16(self, data):
        self._txdata[0] = (self._txdata[0] & 0xf0) | ((data >> 8) & 0x0f)
        self._txdata[1] = (data & 0xff)
        #print(''.join('{:02x}'.format(x) for x in self._txdata))
        try:
            self._cs(0)
            self._spi.write(self._txdata)
        finally:
            self._cs(1)

    def write_uv(self, uv):
        # 4096 is the 12 bits max resolution
        value = int(((uv / 1_000_000) / self._ref) * 4096)
        self.write_u16(value)


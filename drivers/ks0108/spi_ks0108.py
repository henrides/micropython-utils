from machine import Pin
import time

LCD_ON=0x3f
LCD_OFF=0x3e
LCD_DISPLAY_START=0xc0

A_0=0x0001
A_1=0x0002
A_2=0x0004
A_3=0x0008
A_4=0x0010
A_5=0x0020
A_6=0x0040
A_7=0x0080
B_0=0x0100
B_1=0x0200
B_2=0x0400
B_3=0x0800
B_4=0x1000
B_5=0x2000
B_6=0x4000
B_7=0x8000

class SpiKs0108():
    def __init__(self,
                 width, height,
                 ioext,
                 e: Pin,
                 cs: list[int],
                 rs: int,
                 rw: int,
                 reset: int,
                 data: list[int]) -> None:
        self._width = width
        self._height = height
        self._ioext = ioext

        self._pages = height // 8
        self._chips = width // 64

        self._e = e
        self._cs = cs
        self._rs = rs
        self._rw = rw
        self._data = data
        self._reset = reset

        self._write_command_ticks = 0
        self._write_data_ticks = 0
        self._write_data_count = 0
        #self._spi_ticks = 0
        #self._set_data_value_ticks = 0
        self._txdata = 0x0000

    def _set_txdata_bit(self, pin, val):
        if val == 1:
            self._txdata = self._txdata | pin
        else:
            self._txdata = self._txdata & ~pin

    def init(self):
        self._e.init(Pin.OUT)

        self._set_txdata_bit(self._rs, 0)
        self._set_txdata_bit(self._rw, 0)
        self._e.low()

        #if self._reset != None:
        #    self._set_txdata_bit(self._reset)
        #    time.sleep_us(1)
        #    self._reset.low()
        #    time.sleep_us(1)
        #    self._reset.high()

        for i in range(self._chips):
            self._write_command(LCD_ON, i)
            self._write_command(LCD_DISPLAY_START, i)

    def print_buffer(self, buffer):
        start = time.ticks_us()
        self._write_command_ticks = 0
        self._write_data_ticks = 0
        self._write_data_count = 0
        #self._spi_ticks = 0
        #self._set_data_value_ticks = 0
        self._ioext.clear_spi_ticks()
        self._write_framebuffer(buffer)
        print('Spent {}us in write_data ({}) and {}us in write_command for a total time of {}us'.format(self._write_data_ticks, self._write_data_count, self._write_command_ticks, time.ticks_us() - start))
        self._ioext.print_spi_ticks()
        #print('set_data_value {}'.format(self._set_data_value_ticks))
        #print('spi ticks {}'.format(self._spi_ticks))

    def _write_command(self, cmd, chip):
        start = time.ticks_us()
        self._set_cs(chip)
        self._set_txdata_bit(self._rs, 0)
        self._set_txdata_bit(self._rw, 0)

        self._set_data_value(cmd)
        self._ioext.write_gpio(self._txdata)
        self._en()
        self._write_command_ticks += time.ticks_diff(time.ticks_us(), start)

    def _write_data(self, data, chip):
        start = time.ticks_us()
        self._write_data_count += 1
        self._set_cs(chip)
        self._set_txdata_bit(self._rs, 1)
        self._set_txdata_bit(self._rw, 0)

        self._set_data_value(data)
        self._ioext.write_gpio(self._txdata)
        self._en()
        self._write_data_ticks += time.ticks_diff(time.ticks_us(), start)


    def _set_cs(self, chip):
        for i in range(self._chips):
            if i == chip:
                self._set_txdata_bit(self._cs[i], 1)
            else:
                self._set_txdata_bit(self._cs[i], 0)

    def _set_data_value(self, value):
        #start = time.ticks_us()
        for i in range(8):
            self._set_txdata_bit(self._data[i], (value >> i) & 1)
        #self._set_data_value_ticks += time.ticks_us() - start

    def _en(self):
        time.sleep_us(1)
        self._e.high()
        time.sleep_us(1)
        self._e.low()

    def _write_framebuffer(self, buffer):
        # page = 8, chip = 2, pixel width = 64 : 8*2*64 = 1024
        # 1024 _write_data + 32 _write_command = (1024+32)*2us = 2112us
        #print('page {} chips {}'.format(self._pages, self._chips))
        for page in range(self._pages):
            for chip in range(self._chips):
                self._write_command(0xb8 | (0x07 & page), chip)
                self._write_command(0x40, chip)
                self._write_page(buffer, page, chip)
    
    def _write_page(self, buffer, page, chip):
        for i in range(64):
            self._write_data(buffer[i + (64 * chip) + (page * self._width)], chip)

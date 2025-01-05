from machine import Pin, mem32
import time

LCD_ON=0x3f
LCD_OFF=0x3e
LCD_DISPLAY_START=0xc0

class Ks0108():
    def __init__(self,
                 width, height,
                 e: Pin,
                 cs: list[Pin],
                 rs: Pin,
                 rw: Pin,
                 reset: Pin,
                 data: list[Pin]) -> None:
        self._width = width
        self._height = height

        self._pages = height // 8
        self._chips = width // 64

        self._e = e
        self._cs = cs
        self._rs = rs
        self._rw = rw
        self._data = data
        self._reset = reset

    def init(self):
        self._e.init(Pin.OUT)
        self._rs.init(Pin.OUT)
        self._rw.init(Pin.OUT)
        for i in range(self._chips):
            self._cs[i].init(Pin.OUT)

        self._set_data_direction(Pin.OUT)

        self._rs.low()
        self._rw.low()
        self._e.low()

        if self._reset != None:
            self._reset.init(Pin.OUT)
            self._reset.high()
            time.sleep_us(1)
            self._reset.low()
            time.sleep_us(1)
            self._reset.high()

        for i in range(self._chips):
            self._set_cs(i)
            self._write_command(LCD_ON, i)
            self._write_command(LCD_DISPLAY_START, i)

    def print_buffer(self, buffer):
        self._write_framebuffer(buffer)

    def _write_command(self, cmd, chip):
        # No need to wait ready as the code is way slower than the LCD
        #self._wait_ready(chip)
        # ... which mean that we do not need to change the direction
        #self._set_data_direction(Pin.OUT)

        # setting this in the caller to prevent setting them unnecessary
        #self._set_cs(chip)
        #self._rs.low()
        #self._rw.low()

        self._set_data_value(cmd)
        self._en()

    def _write_data(self, data, chip):
        # No need to wait ready as the code is way slower than the LCD
        #self._wait_ready(chip)
        # ... which mean that we do not need to change the direction
        #self._set_data_direction(Pin.OUT)

        # setting this in the caller to prevent setting them unnecessary
        #self._set_cs(chip)
        #self._rs.high()
        #self._rw.low()

        self._set_data_value(data)
        self._en()


    def _wait_ready(self, chip):
        self._set_data_direction(Pin.IN)
        self._set_cs(chip)
        self._rs.low()
        self._rw.high()

        while True:
            self._en()
            if self._data[7].value() == 0 and self._data[4].value() == 0:
                break
            time.sleep_us(1)

    def _set_cs(self, chip):
        for i in range(self._chips):
            if i == chip:
                self._cs[i].high()
            else:
                self._cs[i].low()

    def _set_data_direction(self, dir):
        for i in range(len(self._data)):
            self._data[i].init(dir, Pin.PULL_DOWN)

    def _set_data_value(self, value):
        for i in range(8):
            self._data[i].value((value >> i) & 0x01)

    def _en(self):
        # No need t=for the sleeps as flipping a pin takes longer then the mandatory timing
        #time.sleep_us(1)
        self._e.high()
        #time.sleep_us(1)
        self._e.low()

    def _write_framebuffer(self, buffer):
        self._rw.low()
        for page in range(self._pages):
            for chip in range(self._chips):
                self._set_cs(chip)
                self._rs.low()
                self._write_command(0xb8 | (0x07 & page), chip)
                self._write_command(0x40, chip)
                self._write_page(buffer, page, chip)
    
    def _write_page(self, buffer, page, chip):
        self._rs.high()
        for i in range(64):
            self._write_data(buffer[i + (64 * chip) + (page * self._width)], chip)

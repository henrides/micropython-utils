from machine import Pin
import asyncio
import time
from display_drivers import DisplayDriver

LCD_ON=0x3f
LCD_OFF=0x3e
LCD_DISPLAY_START=0xc0

class AsyncKs0108(DisplayDriver):
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

    async def init(self):
        self._e.init(Pin.OUT)
        self._rs.init(Pin.OUT)
        self._rw.init(Pin.OUT)
        for i in range(self._chips):
            self._cs[i].init(Pin.OUT)

        self._rs.low()
        self._rw.low()
        self._e.low()

        if self._reset != None:
            self._reset.init(Pin.OUT)
            self._reset.high()
            await asyncio.sleep_ms(1)
            self._reset.low()
            await asyncio.sleep_ms(1)
            self._reset.high()

        for i in range(self._chips):
            await self._write_command(LCD_ON, i)
            await self._write_command(LCD_DISPLAY_START, i)

        buffer = bytearray(self._width * (self._height // 8))
        await self._write_framebuffer(buffer)

    async def print_buffer(self, buffer: bytearray):
        await self._write_framebuffer(buffer)

    async def _write_command(self, cmd, chip):
        await self._wait_ready(chip)
        self._set_data_direction(Pin.OUT)
        self._set_cs(chip)
        self._rs.low()
        self._rw.low()

        self._set_data_value(cmd)
        self._en()

    async def _write_data(self, data, chip):
        await self._wait_ready(chip)
        self._set_data_direction(Pin.OUT)
        self._set_cs(chip)
        self._rs.high()
        self._rw.low()

        self._set_data_value(data)
        self._en()


    async def _wait_ready(self, chip):
        self._set_data_direction(Pin.IN)
        self._set_cs(chip)
        self._rs.low()
        self._rw.high()

        while True:
            self._en()
            if self._data[7].value() == 0 and self._data[4].value() == 0:
                break
            await asyncio.sleep_ms(1)

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
            val = (value >> i) & 0x01
            self._data[i].value(val)

    def _en(self):
        time.sleep_us(1)
        self._e.high()
        time.sleep_us(1)
        self._e.low()

    async def _write_framebuffer(self, buffer: bytearray):
        for page in range(self._pages):
            for chip in range(self._chips):
                addr = 0xb8 | (0x07 & page)
                await self._write_command(addr, chip)
                await self._write_command(0x40, chip)
                await self._write_page(buffer, page, chip)
    
    async def _write_page(self, buffer: bytearray, page, chip):
        for i in range(64):
            val = buffer[i + (64 * chip) + (page * self._width)]
            await self._write_data(val, chip)

import rp2
from machine import Pin
import time

# Two state machines: 
#   - data output: sets the data pins and toggles the en pin to latch the data
#   - ctrl output: sets the control pins when starting a transfer and changing page

@rp2.asm_pio(out_init=[rp2.PIO.OUT_LOW] * 8, sideset_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=8, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def ks0108_data_output():
    wrap_target()
    out(pins, 8)    .side(1)    [4]
    nop()           .side(0)    [4]
    wrap()

@rp2.asm_pio(out_init=[rp2.PIO.OUT_LOW] * 4, autopull=True, pull_thresh=4, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def ks0108_ctrl_output():
    wrap_target()
    out(pins, 4)                [4]
    wrap()

LCD_ON=0x3f
LCD_OFF=0x3e
LCD_DISPLAY_START=0xc0
class PioKs0108():
    def __init__(self,
                 width, height,
                 ctrl_first_pin: Pin, # First control pins in the order rw, rs, cs0, cs1
                 en_pin: Pin,
                 data_first_pin: Pin, # First data pin of 8
                 reset: Pin) -> None:
        self._width = width
        self._height = height

        self._pages = height // 8
        self._chips = width // 64

        self._ctrl_first_pin = ctrl_first_pin
        self._en_pin = en_pin
        self._data_first_pin = data_first_pin 
        self._reset = reset

        self._en_pin.init(Pin.OUT)

        self._data_sm = rp2.StateMachine(1, ks0108_data_output, freq=4000000, sideset_base=self._en_pin, out_base=self._data_first_pin)
        self._ctrl_sm = rp2.StateMachine(2, ks0108_ctrl_output, freq=4000000, out_base=self._ctrl_first_pin)

        self._data_sm.active(1)
        self._ctrl_sm.active(1)

    def init(self):
        self._en_pin.low()
        self._ctrl_sm.put(0x0)

        if self._reset != None:
            self._reset.init(Pin.OUT)
            self._reset.high()
            time.sleep_us(1)
            self._reset.low()
            time.sleep_us(1)
            self._reset.high()

        self._ctrl_sm.put(0x4)
        self._data_sm.put(LCD_ON)
        self._data_sm.put(LCD_DISPLAY_START)

        self._ctrl_sm.put(0x8)
        self._data_sm.put(LCD_ON)
        self._data_sm.put(LCD_DISPLAY_START)

    def print_buffer(self, buffer):
        start = time.ticks_us()
        self._write_framebuffer(buffer)
        #print('writing framebuffer took {}us'.format(time.ticks_diff(time.ticks_us(), start)))

    def _write_framebuffer(self, buffer):
        for page in range(self._pages):
            for chip in range(self._chips):
                self._ctrl_sm.put(1 << (chip + 2))
                self._data_sm.put(0xb8 | (0x07 & page))
                self._data_sm.put(0x40)
                self._write_page(buffer, page, chip)
    
    def _write_page(self, buffer, page, chip):
        self._ctrl_sm.put(0x2 | (1 << chip + 2))
        for i in range(64):
            # use DMA instead?
            self._data_sm.put(buffer[i + (64 * chip) + (page * self._width)])

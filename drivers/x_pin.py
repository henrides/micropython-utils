from machine import Pin
import mcp23Sxx

class XPin():
    def __init__(self, ioext, no, dir=Pin.IN, pull=Pin.PULL_UP):
        self._ioext = ioext
        self._no = no
        self._irq_handler = None
        self._irq_trigger = None
        self.init(dir, pull)

    def __call__(self, v=None):
        return self.value(v)

    def init(self, dir=Pin.IN, pull=Pin.PULL_UP):
        self._dir = dir
        self._pull = pull

        flags = mcp23Sxx.IOC_ENABLED|mcp23Sxx.IOC_CMP_PREV if dir == Pin.IN else mcp23Sxx.IOC_DISABLED
        if dir == Pin.IN and pull == Pin.PULL_UP:
            flags |= mcp23Sxx.INPUT_PULLUP

        self._ioext.setup(self._no, dir, flags)

    def value(self, v=None):
        if v != None and dir == Pin.OUT:
            return self._ioext.output(self._no, v)
        else:
            # Do not force a read. The internal values must be updated some other way
            return self._ioext.input_pins([self._no], False)[0]

    def deinit(self):
        pass

    def low(self):
        self.value(0)

    def high(self):
        self.value(1)

    def toggle(self):
        if self() == 1:
            self.value(0)
        else:
            self.value(1)

    def irq(self, handler, trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, *, priority=1, wake=None, hard=False):
        self._irq_handler = handler
        self._irq_trigger = trigger
        self._ioext.registerInterruptHandler(self._no, self._internal_irq)

    def _internal_irq(self, new_val):
        if self._irq_handler != None:
            if new_val and (self._irq_trigger & Pin.IRQ_RISING):
                self._irq_handler(self)
            if not new_val and (self._irq_trigger & Pin.IRQ_FALLING):
                self._irq_handler(self)

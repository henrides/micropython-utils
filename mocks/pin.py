IN = "in"
OUT = "out"
PULL_DOWN = "pull_down"
PULL_UP = "pull_up"

IRQ_FALLING = 0x01
IRQ_RISING = 0x02
IRQ_LOW_LEVEL = 0x04
IRQ_HIGH_LEVEL = 0x08

class Pin():
    IN = IN
    OUT = OUT
    PULL_DOWN = PULL_DOWN
    PULL_UP = PULL_UP
    path = '.'

    def __init__(self, no, dir=IN, pull=PULL_UP):
        self._no = no
        self.init(dir, pull)

    def __call__(self, v=None):
        return self.value(v)

    def init(self, dir=IN, pull=PULL_UP):
        self._dir = dir
        if dir == IN and pull == PULL_UP:
            self.value(1)
        else :
            self.value(0)

    def value(self, v=None):
        if v == None:
            f = open(self._get_filename(), 'r')
            buf = f.read(1)
            f.close()
            return int(buf[0])
        else :
            f = open(self._get_filename(), 'w')
            f.write(str(v))
            f.close()
        return 0

    def _get_filename(self):
        return '{}/pin{}'.format(Pin.path, self._no)

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

    def irq(self, handler, trigger=IRQ_FALLING|IRQ_RISING, *, priority=1, wake=None, hard=False):
        pass

# MCP23Sxx MicroPython Driver - for MCP23Sxx SPI GPIO Expander.
#
# Based on former work of Florian Mueller for Raspberry-Pi
#    Copyright 2016-2019 Florian Mueller (contact@petrockblock.com)
#    https://github.com/petrockblog/RPi-MCP23S17/tree/master/RPiMCP23S17
#
# Aug 13, 2019 : make it compatible with MicroPython against the machine.SPI interface
# Aug 13, 2019 : make it compatible with MicroPython against the machine.SPI interface
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__version__ = '0.0.2'

from time import sleep_us, ticks_us
from machine import Pin

"""Register addresses as documented in the technical data sheet at
http://ww1.microchip.com/downloads/en/DeviceDoc/21952b.pdf
"""
MCP23S17_IODIRA = 0x00
MCP23S17_IODIRB = 0x01
MCP23S17_IPOLA = 0x02
MCP23S17_IPOLB = 0x03
MCP23S17_GPINTENA = 0x04
MCP23S17_GPINTENB = 0x05
MCP23S17_DEFVALA = 0x06
MCP23S17_DEFVALB = 0x07
MCP23S17_INTCONA = 0x08
MCP23S17_INTCONB = 0x09
MCP23S17_IOCON = 0x0A
MCP23S17_GPPUA = 0x0C
MCP23S17_GPPUB = 0x0D
MCP23S17_INTFA = 0x0E
MCP23S17_INTFB = 0x0F
MCP23S17_INTCAPA = 0x10
MCP23S17_INTCAPB = 0x11
MCP23S17_GPIOA = 0x12
MCP23S17_GPIOB = 0x13
MCP23S17_OLATA = 0x14
MCP23S17_OLATB = 0x15

"""Bit field flags as documentined in the technical data sheet at
http://ww1.microchip.com/downloads/en/DeviceDoc/21952b.pdf
"""
IOCON_UNUSED = 0x01
IOCON_INTPOL = 0x02
IOCON_ODR = 0x04
IOCON_HAEN = 0x08
IOCON_DISSLW = 0x10
IOCON_SEQOP = 0x20
IOCON_MIRROR = 0x40
IOCON_BANK_MODE = 0x80

MCP23S17_CMD_WRITE = 0x40
MCP23S17_CMD_READ = 0x41

# Setup flags
INPUT_POL_OPP=0x1
INPUT_POL_SAME=0x2
IOC_ENABLED=0x4
IOC_DISABLED=0x8
IOC_DEF_0=0x10
IOC_DEF_1=0x20
IOC_CMP_DEF=0x40
IOC_CMP_PREV=0x80
INPUT_PULLUP=0x100
INPUT_NO_PULLUP=0x200

class _InterruptSubscription():
    def __init__(self, pin, callback):
        self._pin = pin
        self._callback = callback

    def _isAffected(self, interrupted_pins):
        return self._pin in interrupted_pins

    def __call__(self, values):
        if self._isAffected(values):
            self._callback(values[self._pin])

class MCP23S17(object):
    """ This class provides an abstraction of the GPIO expander MCP23S17 """

    def __init__(self, spi, pin_cs, mode=IOCON_HAEN, pin_int=None, device_id=0x00):
        """ spi : initialized SPI bus (mode 0).
        pin_cs : The Chip Select pin of the MCP.
        mode : The global flags
        pin_int : interrupt pin
        device_id : The device ID of the component, i.e., the hardware address (default 0)
        """
        self._device_id = device_id << 1 # prepare addr for payloads
        self._mode = mode
        self._GPIOA = 0
        self._GPIOB = 0
        self._IODIRA = 0
        self._IODIRB = 0
        self._IPOLA = 0
        self._IPOLB = 0
        self._GPPUA = 0
        self._GPPUB = 0
        self._GPINTENA = 0
        self._GPINTENB = 0
        self._DEFVALA = 0
        self._DEFVALB = 0
        self._INTCONA = 0
        self._INTCONB = 0
        self._pin_reset = -1 # removed from parameters
        #self._bus = bus
        self._pin_cs = pin_cs
        self._pin_int = pin_int
        #self._spimode = 0b00
        self._spi = spi
        if self._pin_int != None:
            self._pin_int.irq(self._irqHandler, Pin.IRQ_FALLING)
            self._interrupt_handlers = []
        self.begin()

    def begin(self):
        #Initializes the MCP23S17 with hardware-address access and sequential operations mode.
        self._writeRegister( MCP23S17_IOCON, self._mode)

        # set defaults
        for index in range(0, 16): # 0 to 15
            self.setup(index, Pin.IN)
            self.pullup(index, True)

    def setup(self, pin, mode, flags=INPUT_POL_SAME|IOC_DISABLED):
        """ Sets the direction for a given pin. """
        # Parameters:
        #  pin -- The pin index (0 - 15)
        #  mode -- The direction of the pin (Pin.In, Pin.OUT)
        #  flags -- ORed list of flags

        self._validate_pin(pin)
        assert ((mode == Pin.IN) or (mode == Pin.OUT))
        
        if (pin < 8):
            self._IODIRA = self._updateRegisterData(self._IODIRA, pin, mode == Pin.IN)
            self._IPOLA = self._updateRegisterData(self._IPOLA, pin, flags & INPUT_POL_OPP)
            self._GPINTENA = self._updateRegisterData(self._GPINTENA, pin, flags & IOC_ENABLED)
            self._DEFVALA = self._updateRegisterData(self._DEFVALA, pin, flags & IOC_DEF_1)
            self._INTCONA = self._updateRegisterData(self._INTCONA, pin, flags & IOC_CMP_DEF)
            self._GPPUA = self._updateRegisterData(self._GPPUA, pin, flags & INPUT_PULLUP)

            self._writeRegister(MCP23S17_IODIRA, self._IODIRA)
            self._writeRegister(MCP23S17_IPOLA, self._IPOLA)
            self._writeRegister(MCP23S17_GPINTENA, self._GPINTENA)
            self._writeRegister(MCP23S17_DEFVALA, self._DEFVALA)
            self._writeRegister(MCP23S17_INTCONA, self._INTCONA)
            self._writeRegister(MCP23S17_GPPUA, self._GPPUA)
        else:
            self._IODIRB = self._updateRegisterData(self._IODIRB, pin, mode == Pin.IN)
            self._IPOLB = self._updateRegisterData(self._IPOLB, pin, flags & INPUT_POL_OPP)
            self._GPINTENB = self._updateRegisterData(self._GPINTENB, pin, flags & IOC_ENABLED)
            self._DEFVALB = self._updateRegisterData(self._DEFVALB, pin, flags & IOC_DEF_1)
            self._INTCONB = self._updateRegisterData(self._INTCONB, pin, flags & IOC_CMP_DEF)
            self._GPPUB = self._updateRegisterData(self._GPPUB, pin, flags & INPUT_PULLUP)

            self._writeRegister(MCP23S17_IODIRB, self._IODIRB)
            self._writeRegister(MCP23S17_IPOLB, self._IPOLB)
            self._writeRegister(MCP23S17_GPINTENB, self._GPINTENB)
            self._writeRegister(MCP23S17_DEFVALB, self._DEFVALB)
            self._writeRegister(MCP23S17_INTCONB, self._INTCONB)
            self._writeRegister(MCP23S17_GPPUB, self._GPPUB)

    def _updateRegisterData(self, data, pin, val):
        pin_mask = self._pinMask(pin)
        if val:
            data |= pin_mask
        else:
            data &= (~pin_mask)
        return data

    def registerInterruptHandler(self, pin, callback):
        self._interrupt_handlers.append(_InterruptSubscription(pin, callback))

    def _irqHandler(self, pin):
        prev_values = self._GPIOB << 8 | self._GPIOA
        new_values = self.read_gpio()
        interrupted_pins = {}
        for i in range(0, 16):
            new_value = (new_values >> i) & 0x1
            if (prev_values >> i) & 0x1 != new_value:
                interrupted_pins[i] = new_value
        for sub in self._interrupt_handlers:
            sub(interrupted_pins)

    def input(self, pin):
        """ Reads the logical level of a given pin. """
        # pin -- The pin index (0 - 15)
        self._validate_pin(pin)

        if (pin < 8):
            self._GPIOA = self._readRegister(MCP23S17_GPIOA)
            if ((self._GPIOA & (1 << pin)) != 0):
                return True
            else:
                return False
        else:
            self._GPIOB = self._readRegister(MCP23S17_GPIOB)
            pin &= 0x07
            if ((self._GPIOB & (1 << pin)) != 0):
                return True
            else:
                return False

    def pullup(self, pin, enabled):
        """ Enables or disables the pull-up mode for input pins. """
        self._validate_pin( pin )

        if pin < 8:
            self._GPPUA = self._updateRegisterData(self._GPPUA, pin, enabled)
            self._writeRegister(MCP23S17_GPPUA, self._GPPUA)
        else:
            self._GPPUB = self._updateRegisterData(self._GPPUB, pin, enabled)
            self._writeRegister(MCP23S17_GPPUB, self._GPPUB)

    def input_pins( self, pins, read=True ):
        """ Read multiple pins and return list of state. Pins = list of pins. Read Force GPIO read"""
        [self._validate_pin(pin) for pin in pins]
        if read:
            # Get GPIO state.
            self.read_gpio()
        # Return True if pin's bit is set.
        r = []
        for pin in pins:
            if (pin < 8):
                if ((self._GPIOA & (1 << pin)) != 0):
                    r.append( True )
                else:
                    r.append( False )
            else:
                pin &= 0x07
                if ((self._GPIOB & (1 << pin)) != 0):
                    r.append( True )
                else:
                    r.append( False )
        # Return the result
        return r

    def output(self, pin, level):
        """ Sets the level of a given pin. """
        # pin -- The pin idnex (0 - 15)
        # level -- The logical level to be set (False, True)
        self._validate_pin( pin )

        if (pin < 8):
            register = MCP23S17_GPIOA
            data = self._GPIOA
        else:
            register = MCP23S17_GPIOB
            data = self._GPIOB

        pin_mask = self._pinMask(pin)
        if level :
            data |= pin_mask
        else:
            data &= (~pin_mask)

        self._writeRegister(register, data)

        if (pin < 8):
            self._GPIOA = data
        else:
            self._GPIOB = data

    def output_pins(self, pins):
        """Sets multiple pins high or low at once.  Pins = dict of pin:state """
        [self._validate_pin(pin) for pin in pins.keys()]
        # Set each changed pin's bit.
        for pin, value in iter(pins.items()):
            if (pin < 8):
                register = MCP23S17_GPIOA
                data = self._GPIOA
            else:
                register = MCP23S17_GPIOB
                data = self._GPIOB

            pin_mask = self._pinMask(pin)
            if value :
                data |= pin_mask
            else:
                data &= (~pin_mask)

            if (pin < 8):
                self._GPIOA = data
            else:
                self._GPIOB = data

        # Write GPIO states.
        buff = (self._GPIOB << 8) | self._GPIOA
        self._writeRegisterWord(MCP23S17_GPIOA, buff )

    def _pinMask(self, pin):
        return 1 << (pin & 0x07)

    def write_gpio(self, data):
        """ Sets the data port value for all pins with a 16 bit values AND send it to the MCP23Sxx """
        self._GPIOA = (data & 0xFF)
        self._GPIOB = (data >> 8)
        self._writeRegisterWord(MCP23S17_GPIOA, data)

    def read_gpio(self):
        """ Reads the data port value of all pins. Store the values internally then returns a 16 bits data """
        data = self._readRegisterWord(MCP23S17_GPIOA)
        self._GPIOA = (data & 0xFF)
        self._GPIOB = (data >> 8)
        return data

    def _writeRegister(self, register, value):
        command = MCP23S17_CMD_WRITE | self._device_id
        self._pin_cs.value( 0 )
        #sleep_us( 1 )
        self._spi.write( bytes([command, register, value]) )
        self._pin_cs.value( 1 )
        #sleep_us( 1 )

    def _readRegister(self, register):
        command = MCP23S17_CMD_READ | self._device_id
        self._pin_cs.value( 0 )
        #sleep_us( 1 )
        #self._setSpiMode(self._spimode)
        self._spi.write( bytes([command, register]) )
        #data = self._spi.xfer2([command, register, 0])
        data = self._spi.read( 1 )
        self._pin_cs.value( 1 )
        #sleep_us( 1 )
        return data[0]# data[2]

    def _readRegisterWord(self, register):
        if self._sequentialOpEnabled():
            command = MCP23S17_CMD_READ | self._device_id
            self._pin_cs.value( 0 )
            self._spi.write( bytes([command, register]) )
            data = self._spi.read( 2 )
            self._pin_cs.value( 1 )
            return data[1] << 8 | data[0]
        buffer = [0, 0]
        buffer[0] = self._readRegister(register)
        buffer[1] = self._readRegister(register + 1)
        return ((buffer[1] << 8) | buffer[0])

    def _writeRegisterWord(self, register, data):
        if self._sequentialOpEnabled():
            command = MCP23S17_CMD_WRITE | self._device_id
            self._pin_cs.value( 0 )
            self._spi.write( bytes([command, register, data & 0xFF, data >> 8]) )
            self._pin_cs.value( 1 )
            return
        self._writeRegister(register, data & 0xFF)
        self._writeRegister(register + 1, data >> 8)

    def _sequentialOpEnabled(self):
        # SEQOP = 1 means sequential operation disabled
        return not (self._mode & IOCON_SEQOP)

    def _validate_pin(self, pin):
        # Raise an exception if pin is outside the range of allowed values.
        if pin < 0 or pin >= 16:
            raise ValueError('Invalid GPIO value, must be between 0 and 15.')

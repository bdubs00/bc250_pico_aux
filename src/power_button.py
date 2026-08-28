from machine import Pin


class PowerButton:
    """Momentary button wired between its pin and GND (active low)."""

    def __init__(self, pin):
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)

    def read(self):
        """Return 1 when released, 0 when pressed."""
        return self._pin.value()


class MotherboardPowerButton:
    """Drive the PC817 that shorts the BC-250 PW signal to ground."""

    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT, value=0)

    def press(self):
        self._pin.value(1)

    def release(self):
        self._pin.value(0)

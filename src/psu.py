from machine import Pin


class PSU:
    """ATX PS_ON# control.

    The pin sinks PS_ON# directly as an open-drain output: driven low
    the PSU turns on; released to high-impedance the PSU's internal
    pull-up returns the line to standby. PS_ON# idles at up to 5.25 V,
    which the RP2350's 5 V-tolerant pads accept while the chip is
    powered; the +5VSB diode feed keeps the chip powered whenever the
    line is live.
    """

    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OPEN_DRAIN, pull=None, value=1)
        self._enabled = False

    def on(self):
        self._pin.value(0)
        self._enabled = True

    def off(self):
        self._pin.value(1)
        self._enabled = False

    @property
    def enabled(self):
        return self._enabled

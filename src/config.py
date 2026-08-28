# Pin map and timing for the Raspberry Pi Pico 2 (RP2350).
# Adjust to match your board.

BUTTON_PIN = 16       # case button to GND; internal pull-up
PS_ON_PIN = 17        # sinks ATX PS_ON# directly; open-drain, low = PSU on
BOARD_BUTTON_PIN = 18 # drives the PC817 LED for the BC-250 PW signal
SENSE_PIN = 15        # BC-250 TPMS1 pin 9 (+3.3 V while the board is on)
                      # Set to None for hard-off toggle mode.

# True: after enabling the PSU, pulse the BC-250 PW signal to start it.
# False: rely on the BC-250 AUTO_PWRON setting; PW is still used for shutdown.
PULSE_PWR_ON_START = True

DEBOUNCE_MS = 30        # button must be stable this long before acting
LONG_PRESS_MS = 5000    # hold this long while on to force power off
POLL_MS = 5             # button polling interval
PSU_SETTLE_MS = 1000     # wait after PS_ON# before pulsing BC-250 PW
BOARD_BUTTON_PULSE_MS = 500
BOOT_TIMEOUT_MS = 15000  # PW pulse released -> expect SENSE high within this
SENSE_DEBOUNCE_MS = 100  # reject short glitches on TPMS1 pin 9
SENSE_CONFIRM_MS = 4000  # SENSE low this long before releasing PS_ON#
SHUTDOWN_TIMEOUT_MS = 120000

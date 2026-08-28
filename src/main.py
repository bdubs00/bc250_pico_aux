import time

from machine import Pin
from micropython import const

from config import (
    BOARD_BUTTON_PIN,
    BOARD_BUTTON_PULSE_MS,
    BOOT_TIMEOUT_MS,
    BUTTON_PIN,
    DEBOUNCE_MS,
    LONG_PRESS_MS,
    POLL_MS,
    PS_ON_PIN,
    PSU_SETTLE_MS,
    PULSE_PWR_ON_START,
    SENSE_CONFIRM_MS,
    SENSE_DEBOUNCE_MS,
    SENSE_PIN,
    SHUTDOWN_TIMEOUT_MS,
)
from power_button import MotherboardPowerButton, PowerButton
from psu import PSU


OFF = const(0)
POWER_ON_SETTLE = const(1)
POWER_ON_PRESS = const(2)
POWER_ON_CONFIRM = const(3)
RUNNING = const(4)
SHUTDOWN_PRESS = const(5)
SHUTDOWN_WAIT = const(6)


sense = Pin(SENSE_PIN, Pin.IN, Pin.PULL_DOWN) if SENSE_PIN is not None else None
psu = PSU(PS_ON_PIN)
board_button = MotherboardPowerButton(BOARD_BUTTON_PIN)
button = PowerButton(BUTTON_PIN)

now = time.ticks_ms()
raw_sense = sense.value() if sense is not None else 0
stable_sense = 0

# Do not start the PSU from a single noisy sample after a controller reset.
if raw_sense:
    sense_confirm_started = now
    while (
        raw_sense
        and time.ticks_diff(time.ticks_ms(), sense_confirm_started)
        < SENSE_DEBOUNCE_MS
    ):
        time.sleep_ms(POLL_MS)
        raw_sense = sense.value()
    stable_sense = raw_sense

now = time.ticks_ms()
sense_changed_at = now

# Reassert PS_ON# if the controller restarted while the board still reports on.
state = RUNNING if stable_sense else OFF
if state == RUNNING:
    psu.on()

state_since = now
low_since = None

button_level = button.read()
button_candidate = button_level
button_changed_at = now
press_started = now if button_level == 0 else None
long_press_handled = False


def enter(new_state):
    global state, state_since, low_since
    state = new_state
    state_since = time.ticks_ms()
    low_since = None


def force_off():
    board_button.release()
    psu.off()
    enter(OFF)


def short_press():
    if state == OFF:
        psu.on()
        enter(POWER_ON_SETTLE)
    elif state == RUNNING:
        if sense is None:
            force_off()
        else:
            board_button.press()
            enter(SHUTDOWN_PRESS)


while True:
    now = time.ticks_ms()

    # Debounce the case button and act on release so one press creates one event.
    raw_button = button.read()
    if raw_button != button_candidate:
        button_candidate = raw_button
        button_changed_at = now
    elif (
        button_candidate != button_level
        and time.ticks_diff(now, button_changed_at) >= DEBOUNCE_MS
    ):
        button_level = button_candidate
        if button_level == 0:
            press_started = now
            long_press_handled = False
        elif press_started is not None:
            if not long_press_handled:
                short_press()
            press_started = None
            long_press_handled = False

    if (
        press_started is not None
        and not long_press_handled
        and time.ticks_diff(now, press_started) >= LONG_PRESS_MS
    ):
        force_off()
        long_press_handled = True

    # Debounce the board-running indication independently from the button.
    if sense is not None:
        sensed = sense.value()
        if sensed != raw_sense:
            raw_sense = sensed
            sense_changed_at = now
        elif (
            sensed != stable_sense
            and time.ticks_diff(now, sense_changed_at) >= SENSE_DEBOUNCE_MS
        ):
            stable_sense = sensed

    if state == POWER_ON_SETTLE:
        # If AUTO_PWRON already started the board, do not send a second press.
        if sense is not None and stable_sense:
            enter(RUNNING)
        elif (
            (sense is None or raw_sense == 0)
            and time.ticks_diff(now, state_since) >= PSU_SETTLE_MS
        ):
            if PULSE_PWR_ON_START:
                board_button.press()
                enter(POWER_ON_PRESS)
            else:
                enter(POWER_ON_CONFIRM)

    elif state == POWER_ON_PRESS:
        if time.ticks_diff(now, state_since) >= BOARD_BUTTON_PULSE_MS:
            board_button.release()
            enter(POWER_ON_CONFIRM)

    elif state == POWER_ON_CONFIRM:
        if sense is None or stable_sense:
            enter(RUNNING)
        elif (
            raw_sense == 0
            and time.ticks_diff(now, state_since) >= BOOT_TIMEOUT_MS
        ):
            force_off()

    elif state == RUNNING:
        if sense is not None and not stable_sense:
            if low_since is None:
                low_since = now
            elif time.ticks_diff(now, low_since) >= SENSE_CONFIRM_MS:
                force_off()
        else:
            low_since = None

    elif state == SHUTDOWN_PRESS:
        if time.ticks_diff(now, state_since) >= BOARD_BUTTON_PULSE_MS:
            board_button.release()
            enter(SHUTDOWN_WAIT)

    elif state == SHUTDOWN_WAIT:
        if time.ticks_diff(now, state_since) >= SHUTDOWN_TIMEOUT_MS:
            force_off()
        elif not stable_sense:
            if low_since is None:
                low_since = now
            elif time.ticks_diff(now, low_since) >= SENSE_CONFIRM_MS:
                force_off()
        else:
            low_since = None

    time.sleep_ms(POLL_MS)

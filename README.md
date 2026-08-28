# bc250 pico aux

Auxiliary power controller for the AMD ASRock BC-250 using a Raspberry Pi
Pico 2 and a standard ATX PSU. The Pico remains powered from `+5VSB`, controls
ATX `PS_ON#`, pulses the BC-250 power-button input, and watches the BC-250's
running-state signal.

The power sequence is adapted from
[GreatApo/BC250_ESP32_ATX_PSU](https://github.com/GreatApo/BC250_ESP32_ATX_PSU).

> [!WARNING]
> Incorrect ATX or BC-250 wiring can damage the Pico, motherboard, or PSU.
> Disconnect mains and USB before changing wiring, verify connector orientation
> and diode polarity, and check every connection with a multimeter. The Pico
> is live whenever the PSU is plugged in because it is powered by `+5VSB`.

## How it works

The physical case button is connected only to the Pico. A PC817 optocoupler
lets GP18 simulate a separate BC-250 power-button press while keeping that
signal isolated from the GPIO. The case button is not electrically tied to the
BC-250 button signal.

Power on:

1. Release a short case-button press.
2. Pull ATX `PS_ON#` low to start the PSU.
3. Wait 1 second for the main rails to settle.
4. Pulse the BC-250 `PW` signal low for 500 ms.
5. Wait up to 15 seconds for TPMS1 pin 9 to report that the board is on.
6. Cut power again if startup is not confirmed.

Normal shutdown:

1. Release a short case-button press while running.
2. Pulse the BC-250 `PW` signal low for 500 ms, generating its normal ACPI
   power-button event.
3. Keep the PSU on while Linux shuts down.
4. Release `PS_ON#` after TPMS1 pin 9 remains low for 4 seconds.

Holding the case button for at least 5 seconds releases `PS_ON#` immediately.
This is a hard power cut and can cause data loss. An OS-initiated shutdown is
also followed automatically when TPMS1 pin 9 goes low.

If the sense wire is omitted and `SENSE_PIN = None`, startup is assumed after
the power sequence. The next short press releases `PS_ON#` immediately instead
of attempting a graceful shutdown.

## Bill of materials

| Qty | Part | Notes |
| ---: | ---- | ----- |
| 1 | Raspberry Pi Pico 2 (RP2350) | Runs MicroPython |
| 1 | Momentary push button (NO) | Case power button |
| 1 | PC817 optocoupler | Isolated BC-250 `PW` switch |
| 1 | 470 Ohm resistor | GP18-to-PC817 LED current limiting |
| 1 | Series diode: 1N5817/SS14 Schottky, or any silicon rectifier such as 1N400x/1N4148 | `+5VSB`-to-VSYS feed; lets USB and standby power coexist |
| 1 | Suitable TPMS1 connector | TPMS1 is a 2.0 mm-pitch header, not standard 2.54 mm Dupont pitch |
| optional | 8.2 kOhm resistor | External GP15 pull-down, only for original A2-stepping RP2350 erratum E9; see below |
| as needed | Insulated hookup wire and connectors | Add strain relief; do not insert loose bare wires into the ATX connector |

No transistor is needed for `PS_ON#`; GP17 sinks it directly as described under
Wiring. Do not omit the PC817 LED resistor. At 3.3 V, 470 Ohm supplies
approximately 4.5 mA to the optocoupler LED. Because PC817 current-transfer
ratio varies by manufacturer and grade, verify the assembled output voltage as
described in the installation steps.

## Wiring

The Pico GPIO numbers below are logical GP numbers; the values in parentheses
are physical header pins.

| Function | Pico 2 connection | Other connection |
| -------- | ----------------- | ---------------- |
| Case button | GP16 (pin 21), internal pull-up | Normally-open button from GP16 to GND only |
| PSU drive | GP17 (pin 22), direct wire | ATX motherboard-side 24-pin connector pin 16, green `PS_ON#` |
| BC-250 button drive | GP18 (pin 24) through 470 Ohm | PC817 LED anode, pin 1 |
| Running sense | GP15 (pin 20) | TPMS1 pin 9, nominally 3.3 V while running |
| Standby power | VSYS (pin 39) | ATX pin 9/purple `+5VSB` through the Schottky diode, anode toward the PSU |
| Common ground | Any Pico GND, such as pin 38 | ATX black ground and TPMS1 pin 17 |

GP17 sinks `PS_ON#` directly. The firmware configures it as an open-drain
output: driven low, the PSU turns on; released to high-impedance, the PSU's
internal pull-up returns the line to standby. The ATX specification only
requires sinking about 1.6 mA below 0.8 V, and the line idles at no more than
5.25 V, which the RP2350's 5 V-tolerant digital pads (GP0-GP25) accept as long
as the chip is powered. The `+5VSB` diode feed guarantees that condition:
whenever mains is present and `PS_ON#` is live, the Pico is powered.

The PC817 controls the BC-250 power-button input:

| PC817 pin | Connect to |
| --------- | ---------- |
| 1, LED anode | GP18 through 470 Ohm |
| 2, LED cathode | Pico GND |
| 3, phototransistor emitter | TPMS1 pin 17/BC-250 ground |
| 4, phototransistor collector | BC-250 `PW` power-button solder point |


The PC817 is deliberately kept even though both boards share a common ground:
its output is a dry, level-agnostic contact on the BC-250's unbuffered `PW`
solder point, so no Pico fault or firmware bug can present a foreign voltage
to that net, and the pad's pull-up strength never has to be characterized. It
is the only active component besides the Pico itself.

Early RP2350 A2 silicon has erratum E9: a high-impedance input can remain at an
intermediate voltage that overpowers the internal pull-down. The A4 stepping
(shipping in Pico 2 boards from roughly mid-2025 onward) fixes E9, so most
boards need nothing here. If the Pico 2 uses A2 silicon and TPMS1 pin 9 floats
when off, add 8.2 kOhm or less from GP15 to GND. Before relying on that
workaround, verify TPMS1 pin 9 still reads above 2.0 V while running; otherwise
use a buffered sense circuit or A4 silicon.

### Connection diagram

```text
                                 Raspberry Pi Pico 2

 Case button       GND ----------o/ o---------- GP16 (21)

 PSU control       GP17 (22) ------------ ATX PS_ON# pin 16
                   (open-drain: low = PSU on, released = off)

 BC-250 control    GP18 (24) --[470]-- PC817 pin 1 (LED anode)
                   GND (38) ------------ PC817 pin 2 (LED cathode)
                   BC-250 PW ----------- PC817 pin 4 (collector)
                   TPMS1 pin 17 / GND -- PC817 pin 3 (emitter)

 State sense       TPMS1 pin 9 ---------- GP15 (20)

 Standby power     ATX pin 9 +5VSB --[>|- diode]-- VSYS (39)
                   ATX black GND -------- GND (38)
```

The series Schottky diode lets USB and `+5VSB` be connected at the same time:
whichever supply is higher feeds VSYS, and the diode stops USB from
back-feeding the PSU's unpowered standby rail. Its drop leaves VSYS around
4.8 V, well inside the 1.8-5.5 V range, and this is the Pico datasheet's
recommended way to combine an external 5 V source with USB. A suitably rated
ordinary silicon diode also works; its larger drop still leaves VSYS within
range. Do not connect `+5VSB` to VSYS without the diode.

VSYS powers the Pico's onboard 3.3 V regulator; do not connect `+5VSB` to
`3V3(OUT)` or a GPIO.

ATX pin numbers refer to the motherboard-side 24-pin connector. Modular PSU-side
connectors are not standardized and must never be wired from this pin numbering.
Verify pin position and wire function for the specific PSU rather than relying
only on wire color.


## Startup mode


```python
PULSE_PWR_ON_START = True
```

Use this when the BC-250 waits for its `PW` input after the PSU starts. Configure
`AUTO_PWRON1` so the board does not independently auto-start. If TPMS1 pin 9
already rises during the 1-second settle delay, the firmware treats the board
as running and skips the pulse to avoid immediately turning it off again.

Alternatively:

```python
PULSE_PWR_ON_START = False
```

Use this when `AUTO_PWRON1` is configured to start the BC-250 as soon as the PSU
rails appear. The GP18 circuit is still used to request normal shutdown.

## Pin and timing configuration

The defaults in `src/config.py` are:

| Setting | Default | Purpose |
| ------- | ------: | ------- |
| `SENSE_PIN` | GP15 | TPMS1 pin 9 running indication |
| `BUTTON_PIN` | GP16 | Physical case button |
| `PS_ON_PIN` | GP17 | Open-drain ATX `PS_ON#` control |
| `BOARD_BUTTON_PIN` | GP18 | PC817 LED drive for BC-250 button control |
| `PSU_SETTLE_MS` | 1000 ms | Delay before a startup `PW` pulse |
| `BOARD_BUTTON_PULSE_MS` | 500 ms | Simulated BC-250 button press |
| `BOOT_TIMEOUT_MS` | 15000 ms | Startup confirmation timeout |
| `SENSE_DEBOUNCE_MS` | 100 ms | TPMS1 glitch filtering |
| `SENSE_CONFIRM_MS` | 4000 ms | Confirmed-off delay |
| `SHUTDOWN_TIMEOUT_MS` | 120000 ms | Maximum graceful-shutdown wait |
| `LONG_PRESS_MS` | 5000 ms | Forced-cut hold time |

On boot, the firmware requires TPMS1 pin 9 to remain high for 100 ms before it
reasserts `PS_ON#`. This rejects a noisy startup sample, but it is not an
uninterrupted-power guarantee: resetting, reflashing, or crashing the Pico while
the BC-250 is running can still hard-cut the PSU. Only deploy firmware while the
BC-250 is off.

## Installation and test

1. Flash MicroPython for Pico 2 from
   <https://micropython.org/download/RPI_PICO2/>.
2. Install mpremote with `python -m pip install mpremote`.
3. Connect USB and deploy using `make deploy` with the PSU and BC-250 control
   wires disconnected. Verify GP18 defaults low and GP17 idles released
   (high resistance from GP17 to GND, not a driven low).
4. Use a current-limited bench supply or the protected `+5VSB` connection to
   test the Pico-side circuit before attaching the `PS_ON#` wire or PC817
   output.
5. Disconnect mains and USB, connect the ATX and BC-250 control signals, then
   check continuity, shorts, diode orientation, and idle output states.
6. With mains connected and the BC-250 still off, hold BOOTSEL and reset the
   Pico once; confirm the PSU stays off while the pad's default pull-down
   loads `PS_ON#`.
7. During the first controlled startup, monitor the PC817 collector and verify
   it pulls `PW` below 0.4 V relative to TPMS1 pin 17 during the pulse, then
   returns to the released voltage.
8. Test power-on, OS shutdown, startup timeout, and the long-press emergency
   cut while monitoring TPMS1 pin 9.
9. Open the MicroPython REPL with `make monitor` whenever needed; the series
   diode makes simultaneous USB and standby power safe. Deploy firmware only
   while the BC-250 is off, because a Pico reset releases `PS_ON#`.

## Project layout

```text
src/
  main.py         debounced button and power-sequencing state machine
  power_button.py physical-button input and PC817 BC-250 PW output
  psu.py          ATX PS_ON# open-drain output
  config.py       pin map, startup mode, and timings
Makefile          mpremote deploy and monitor helpers
```

AI disclosure: This software was developed with assistance from Qwen 3.8 27B.

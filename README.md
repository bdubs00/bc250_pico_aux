# bc250 pico aux

This project is an auxiliary power controller for the AMD ASRock BC-250. It uses a Raspberry Pi Pico 2 and a standard ATX power supply (PSU). The Pico stays powered from `+5VSB`. It controls the ATX `PS_ON#` line. It pulses the BC-250 power-button input. It watches the running-state signal from the BC-250.

This project adapts the power sequence from [GreatApo/BC250_ESP32_ATX_PSU](https://github.com/GreatApo/BC250_ESP32_ATX_PSU).

> [!WARNING]
> Disconnect mains and USB before you change the wiring.
> The Pico is live whenever the PSU is plugged in, because `+5VSB` powers the Pico.
> Incorrect ATX or BC-250 wiring can damage the Pico, the motherboard, or the PSU.
> Make sure that the connector orientation is correct.
> Make sure that the diode polarity is correct.
> Make sure that every connection is correct with a multimeter.

## How it works

The physical case button connects only to the Pico. A PC817 optocoupler isolates the BC-250 button signal from the GPIO. GP18 drives the optocoupler to simulate a separate BC-250 power-button press. The case button has no electrical connection to the BC-250 button signal.

Power on:

1. A short press of the case button starts the sequence.
2. The firmware pulls ATX `PS_ON#` low to start the PSU.
3. It waits 1 second for the main rails to settle.
4. It pulses the BC-250 `PW` signal low for 500 ms.
5. It waits up to 15 seconds for TPMS1 pin 9 to show that the board is on.
6. If the board does not report startup, it turns the PSU off again.

Normal shutdown:

1. A short press of the case button starts the shutdown, while the board is on.
2. The firmware pulses the BC-250 `PW` signal low for 500 ms.
3. The board gets its normal ACPI power-button event.
4. The firmware keeps the PSU on while Linux shuts down.
5. The firmware releases `PS_ON#` after TPMS1 pin 9 stays low for 4 seconds.

If you hold the case button for at least 5 seconds, the firmware releases `PS_ON#` immediately.  When TPMS1 pin 9 goes low after an OS-initiated shutdown, the firmware also releases `PS_ON#`.

If you omit the sense wire and set `SENSE_PIN = None`, the firmware assumes that startup succeeded after the power sequence. The next short press releases `PS_ON#` immediately. The firmware does not run a graceful shutdown.

## Bill of materials

| Qty | Part | Notes |
| ---: | ---- | ----- |
| 1 | Raspberry Pi Pico 2 (RP2350) | Runs MicroPython |
| 1 | Momentary push button (NO) | Case power button |
| 1 | PC817 optocoupler | Isolated BC-250 `PW` switch |
| 1 | 470 Ohm resistor | GP18-to-PC817 LED current limiting |
| 1 | Series diode: 1N5817/SS14 Schottky, or a silicon rectifier, for example 1N400x/1N4148 | Feed from `+5VSB` to VSYS. Lets USB and standby power coexist. |
| 1 | Suitable TPMS1 connector | TPMS1 is a 2.0 mm-pitch header, not standard 2.54 mm Dupont pitch |
| optional | 8.2 kOhm resistor | External GP15 pull-down. For the original A2-stepping RP2350 erratum E9 only. See the Wiring section. |
| as needed | Insulated hookup wire and connectors | Add strain relief. Do not put loose bare wires into the ATX connector. |

No transistor is needed for `PS_ON#`. GP17 sinks it directly, as described in the Wiring section. Do not omit the PC817 LED resistor. At 3.3 V, the 470 Ohm resistor supplies approximately 4.5 mA to the optocoupler LED. The PC817 current-transfer ratio varies by manufacturer and grade. Make sure that the assembled output voltage is correct. The Installation and test section gives the method.

## Wiring

The GPIO numbers in this table are logical GP numbers. The values in parentheses are physical header pins.

| Function | Pico 2 connection | Other connection |
| -------- | ----------------- | ---------------- |
| Case button | GP16 (pin 21), internal pull-up | Normally-open button from GP16 to GND only |
| PSU drive | GP17 (pin 22), direct wire | ATX motherboard-side 24-pin connector pin 16, green `PS_ON#` |
| BC-250 button drive | GP18 (pin 24) through 470 Ohm | PC817 LED anode, pin 1 |
| Running sense | GP15 (pin 20) | TPMS1 pin 9, nominally 3.3 V while the board is on |
| Standby power | VSYS (pin 39) | ATX pin 9/purple `+5VSB` through the Schottky diode, anode toward the PSU |
| Common ground | Any Pico GND pin, for example pin 38 | ATX black ground and TPMS1 pin 17 |

GP17 sinks `PS_ON#` directly. The firmware configures it as an open-drain output. When GP17 drives the line low, the PSU turns on. When GP17 releases the line to high-impedance, the internal pull-up of the PSU returns it to standby. The ATX specification requires about 1.6 mA of sink current below 0.8 V. The line idles at no more than 5.25 V. The 5 V tolerant digital pads (GP0-GP25) of the RP2350 accept this voltage, as long as the chip is powered. The `+5VSB` diode feed makes sure that the Pico is powered whenever mains is present and `PS_ON#` is live.

The PC817 controls the BC-250 power-button input:

| PC817 pin | Connect to |
| --------- | ---------- |
| 1, LED anode | GP18 through 470 Ohm |
| 2, LED cathode | Pico GND |
| 3, phototransistor emitter | TPMS1 pin 17/BC-250 ground |
| 4, phototransistor collector | BC-250 `PW` power-button solder point |

Both boards share a common ground, but the design keeps the PC817. Its output is a dry, level-agnostic contact on the unbuffered `PW` solder point of the BC-250. No Pico fault or firmware bug can put a foreign voltage on that net. The dry contact removes the need to characterize the pad pull-up. The PC817 is the only active component besides the Pico.

Early RP2350 A2 silicon has erratum E9. A high-impedance input can remain at an intermediate voltage that overpowers the internal pull-down. The A4 stepping (shipping in Pico 2 boards from roughly mid-2025 onward) fixes E9. As a result, most boards need no change here. If the Pico 2 has A2 silicon and TPMS1 pin 9 floats when off, add a pull-down on GP15. Use 8.2 kOhm or less. Before you use that workaround, make sure that TPMS1 pin 9 still reads above 2.0 V while the board is on. If the voltage is less than 2.0 V, use a buffered sense circuit or A4 silicon.

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

The series Schottky diode lets you connect USB and `+5VSB` at the same time. The higher supply feeds VSYS. The diode stops USB from feeding back into the unpowered standby rail of the PSU. The diode drop leaves VSYS around 4.8 V. That value is well inside the 1.8-5.5 V range. The Pico datasheet recommends this way to combine an external 5 V source with USB. An ordinary silicon diode with the right rating also works. Its larger drop still leaves VSYS within range. Do not connect `+5VSB` to VSYS without the diode.

VSYS powers the onboard 3.3 V regulator of the Pico. Do not connect `+5VSB` to `3V3(OUT)` or a GPIO.

ATX pin numbers refer to the motherboard-side 24-pin connector. Never wire modular PSU-side connectors from this pin numbering. Make sure that the pin position and wire function are correct for your PSU. Do not rely on wire color only.

## Startup mode

```python
PULSE_PWR_ON_START = True
```

When the BC-250 waits for its `PW` input after the PSU starts, use this setting. Configure `AUTO_PWRON1` so the board does not independently auto-start. If TPMS1 pin 9 already rises during the 1-second settle delay, the firmware treats the board as on. The firmware skips the pulse to prevent an immediate turn-off.

Alternatively:

```python
PULSE_PWR_ON_START = False
```

When `AUTO_PWRON1` starts the BC-250 as soon as the PSU rails appear, use this setting. The GP18 circuit still requests a normal shutdown.

## Pin and timing settings

The default settings in `src/config.py` are:

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

On boot, the firmware requires TPMS1 pin 9 to remain high for 100 ms before it reasserts `PS_ON#`. This rejects a noisy startup sample, but it is not an uninterrupted-power guarantee. Deploy firmware only while the BC-250 is off. A reset, reflash, or crash of the Pico can still hard-cut the PSU while the BC-250 is on.

## Installation and test

1. Flash MicroPython for Pico 2 from <https://micropython.org/download/RPI_PICO2/>.
2. Install mpremote with `python -m pip install mpremote`.
3. Connect USB. Deploy with `make deploy` while the PSU and BC-250 control wires are disconnected. Make sure that GP18 defaults low. Make sure that GP17 idles released (high resistance from GP17 to GND, not a driven low).
4. Power the Pico-side circuit with a current-limited bench supply or the protected `+5VSB` connection. Make sure that the circuit is correct before you attach the `PS_ON#` wire or the PC817 output.
5. Disconnect mains and USB. Connect the ATX and BC-250 control signals. Make sure that each connection shows the correct continuity. Make sure that there are no shorts. Make sure that the diode orientation is correct. Make sure that the idle output states are correct.
6. When mains is connected and the BC-250 is still off, hold BOOTSEL and reset the Pico once. Make sure that the PSU stays off, while the default pull-down of the pad loads `PS_ON#`.
7. During the first controlled startup, monitor the PC817 collector. Make sure that it pulls `PW` below 0.4 V relative to TPMS1 pin 17 during the pulse. Make sure that it then returns to the released voltage.
8. Run a test of power-on, OS shutdown, startup timeout, and the long-press emergency cut. Monitor TPMS1 pin 9 during the test.
9. Open the MicroPython REPL with `make monitor` when you need it. The series diode makes USB and standby power safe at the same time. Deploy firmware only while the BC-250 is off. A Pico reset releases `PS_ON#`.

## Project layout

```text
src/
  main.py         debounced button and power-sequencing state machine
  power_button.py physical-button input and PC817 BC-250 PW output
  psu.py          ATX PS_ON# open-drain output
  config.py       pin map, startup mode, and timings
Makefile          mpremote deploy and monitor helpers
```

AI disclosure: Qwen 3.8 27B helped develop this software.

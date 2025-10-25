# pH Sensor Calibration and Monitoring (MicroPython)

This repository contains two MicroPython scripts intended for use with the
Gravity: Analog pH Sensor/Meter Kit V2 connected to a Raspberry Pi Pico W.
Upload the scripts to the board from Thonny.

## Files

- `calibrate_ph_sensor.py` — Guides you through a two- or three-point
  calibration using the buffer solutions provided with the Gravity kit. The
  script prints the linear calibration parameters and stores them in
  `ph_calibration.json` on the Pico W.
- `ph_monitor.py` — Continuously measures pH using the stored calibration data
  (or manually supplied parameters) and prints one reading per hour.

## Calibration workflow

1. Wire the Gravity pH interface board's analog output to GP26 (ADC0) on the
   Pico W. Power the sensor board using 5V and GND. Allow the probe to warm up
   in the storage solution for at least 15 minutes.
2. Run `calibrate_ph_sensor.py` from Thonny's Run menu while the Pico W is
   connected. Follow the prompts to measure each reference buffer. Two buffers
   are required; a third buffer (for example, pH 4.00, 7.00, and 10.00) improves
   the linear regression.
3. After the final buffer is recorded, note the printed `slope` and `intercept`
   values. A `ph_calibration.json` file will also be written to the board with
   the captured data.

## Continuous monitoring workflow

1. Transfer `ph_monitor.py` to the Pico W.
2. If `ph_calibration.json` exists on the board (created by the calibration
   script), `ph_monitor.py` will load the `slope` and `intercept` automatically.
   Otherwise, edit the `MANUAL_SLOPE` and `MANUAL_INTERCEPT` constants near the
   top of the script with the values printed during calibration.
3. Run `ph_monitor.py`. The script averages sensor readings for 10 seconds,
   converts the voltage to pH using the calibration parameters, and prints the
   result once per hour along with the measured voltage and standard deviation.
4. Stop the script from Thonny when you want to end logging.

## Notes

- Rinse the probe with distilled water and blot it dry between buffer and sample
  measurements.
- Keep the probe hydrated according to the manufacturer's instructions to avoid
  drift.
- If you plan to reset the Pico W or share the calibration file across boards,
  copy the generated `ph_calibration.json` to your computer using Thonny's file
  browser.

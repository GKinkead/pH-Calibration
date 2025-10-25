"""MicroPython calibration script for the Gravity Analog pH Sensor (V2).

Run this file from Thonny while connected to a Raspberry Pi Pico W. The script
will walk you through collecting voltage readings from two or three reference
buffer solutions and will compute linear calibration parameters for later use.
The computed parameters are saved to ``ph_calibration.json`` on the board so
that measurement scripts can use them directly.
"""

import machine
import ujson
import utime

# ---- Hardware configuration -------------------------------------------------
# ADC pin connected to the pH sensor output. GP26 corresponds to ADC0 on the Pico.
ADC_PIN = 26

# Number of raw ADC samples to average for each voltage reading.
SAMPLES_PER_READING = 20
# Delay (in milliseconds) between raw ADC samples while averaging.
SAMPLE_DELAY_MS = 50
# Duration (in seconds) to collect averaged readings for each buffer solution.
READ_DURATION_S = 15

# File written to the Pico's filesystem with the calculated calibration values.
CALIBRATION_FILE = "ph_calibration.json"

_adc = machine.ADC(ADC_PIN)
_CONVERSION_FACTOR = 3.3 / 65535  # Convert 16-bit reading to volts.


def _read_averaged_voltage(samples=SAMPLES_PER_READING, delay_ms=SAMPLE_DELAY_MS):
    """Return the average voltage across ``samples`` ADC readings."""
    total = 0
    for _ in range(samples):
        total += _adc.read_u16()
        utime.sleep_ms(delay_ms)
    return (total / samples) * _CONVERSION_FACTOR


def _collect_buffer_reading(buffer_ph):
    """Collect averaged voltage samples for the provided buffer solution."""
    print("Collecting samples for pH {:.2f}...".format(buffer_ph))
    deadline = utime.ticks_add(utime.ticks_ms(), int(READ_DURATION_S * 1000))
    voltages = []

    while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
        voltages.append(_read_averaged_voltage())

    average_voltage = sum(voltages) / len(voltages)
    variance = sum((v - average_voltage) ** 2 for v in voltages) / len(voltages)
    stdev = variance ** 0.5

    print(
        "  -> {} readings captured. Average: {:.4f} V, Std Dev: {:.2f} mV".format(
            len(voltages), average_voltage, stdev * 1000
        )
    )
    return average_voltage, stdev, voltages


def _prompt_float(prompt):
    while True:
        try:
            value = input(prompt)
            return float(value)
        except ValueError:
            print("Please enter a numeric value.")


def _choose_point_count():
    while True:
        try:
            count = int(input("How many calibration buffers will you use (2 or 3)? "))
        except ValueError:
            print("Please enter 2 or 3.")
            continue

        if count in (2, 3):
            return count
        print("Calibration requires at least two buffers and no more than three.")


def _compute_linear_fit(points):
    """Return (slope, intercept, r_squared) for pH = slope * voltage + intercept."""
    voltages = [p[0] for p in points]
    ph_values = [p[1] for p in points]

    if len(points) == 2:
        # Straight-line fit through two points.
        v1, v2 = voltages
        if abs(v2 - v1) < 1e-6:
            raise ValueError("Voltage readings for the two buffers were identical.")
        slope = (ph_values[1] - ph_values[0]) / (v2 - v1)
        intercept = ph_values[0] - slope * v1
        # Perfect fit for two points.
        r_squared = 1.0
        return slope, intercept, r_squared

    # Three-point linear regression (least squares).
    mean_v = sum(voltages) / len(points)
    mean_ph = sum(ph_values) / len(points)

    numerator = sum((v - mean_v) * (ph - mean_ph) for v, ph in points)
    denominator = sum((v - mean_v) ** 2 for v in voltages)
    if abs(denominator) < 1e-9:
        raise ValueError("Insufficient voltage variation across buffers.")

    slope = numerator / denominator
    intercept = mean_ph - slope * mean_v

    ss_tot = sum((ph - mean_ph) ** 2 for ph in ph_values)
    ss_res = sum((ph - (slope * v + intercept)) ** 2 for v, ph in points)
    r_squared = 1.0 if ss_tot == 0 else 1 - (ss_res / ss_tot)
    return slope, intercept, r_squared


def _store_calibration(calibration):
    try:
        with open(CALIBRATION_FILE, "w") as file:
            ujson.dump(calibration, file)
        print("Calibration saved to {}".format(CALIBRATION_FILE))
    except OSError as exc:
        print("WARNING: Unable to save calibration file: {}".format(exc))


def main():
    print("\nGravity pH Sensor Calibration")
    print("--------------------------------")
    print(
        "Connect the sensor output to GP26 (ADC0) and ensure the sensor has been"
        " powered for at least 15 minutes before calibrating. Rinse the probe"
        " with distilled water and gently blot dry between each buffer solution."
    )

    point_count = _choose_point_count()
    calibration_points = []

    for idx in range(1, point_count + 1):
        buffer_ph = _prompt_float("Enter the certified pH of buffer #{}: ".format(idx))
        input(
            "Immerse the probe in the pH {:.2f} buffer and press Enter when the"
            " reading is stable...".format(buffer_ph)
        )
        avg_voltage, stdev, _ = _collect_buffer_reading(buffer_ph)
        calibration_points.append((avg_voltage, buffer_ph))

    temperature_input = input(
        "Enter the solution temperature in °C (optional, press Enter to skip): "
    )
    solution_temperature = None
    if temperature_input.strip():
        try:
            solution_temperature = float(temperature_input)
        except ValueError:
            print("Temperature entry ignored (not a number).")

    try:
        slope, intercept, r_squared = _compute_linear_fit(calibration_points)
    except ValueError as exc:
        print("Calibration failed: {}".format(exc))
        return

    print("\nCalibration complete!")
    print("    slope     = {:.6f}".format(slope))
    print("    intercept = {:.6f}".format(intercept))
    print("    r^2       = {:.4f}".format(r_squared))
    print(
        "Copy these values into your measurement script or rely on the generated"
        " ph_calibration.json file."
    )

    calibration = {
        "slope": slope,
        "intercept": intercept,
        "points": [
            {"voltage": point[0], "ph": point[1]} for point in calibration_points
        ],
        "temperature_c": solution_temperature,
        "timestamp": utime.time(),
    }
    _store_calibration(calibration)


if __name__ == "__main__":
    main()

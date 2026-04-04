#!/usr/bin/env python3
"""
Author: Omid Madani

Bench validation script for PWM-to-RPM verification on an embedded thermal control system.

Features:
- CLI-driven execution
- CSV logging
- Optional fault simulation for dry-run and negative testing

Normal DUT assumptions:
- The device under test (DUT) exposes a simple serial CLI.
- Commands:
    SET_PWM <percent>
    GET_RPM
- Responses:
    OK
    RPM:<integer>

This script is intentionally written as test automation code, not product firmware.
It is suitable for bench validation or CI execution against real hardware.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import serial  # pyserial
except ImportError:
    serial = None

# Data structure for defining one test case: PWM setting, expected RPM, and allowed tolerance
@dataclass
class TestPoint:
    pwm_percent: int
    expected_rpm: int
    tolerance_percent: float

# Abstract interface for Device Under Test (DUT)
# Allows switching between real hardware and simulated DUT without changing test logic
class DUTInterface:
    def close(self) -> None:
        pass

    def set_pwm(self, pwm_percent: int) -> None:
        raise NotImplementedError

    def get_rpm(self) -> int:
        raise NotImplementedError

# Real hardware implementation using UART/serial communication
# Sends commands to firmware and reads back responses
class SerialDUT(DUTInterface):
    def __init__(self, port: str, baudrate: int, timeout: float = 1.5) -> None:
        if serial is None:
            raise SystemExit("pyserial is required. Install with: pip install pyserial")
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    def close(self) -> None:
        self.ser.close()

    def send_command(self, command: str) -> str:
        self.ser.reset_input_buffer()
        # Send command to DUT (newline-terminated protocol)
        self.ser.write((command.strip() + "\n").encode("utf-8"))
        self.ser.flush()
        # Read single-line response from DUT (blocking until timeout or data received)
        response = self.ser.readline().decode("utf-8", errors="replace").strip()
        if not response:
            raise RuntimeError(f"No response for command: {command}")
        return response

    def set_pwm(self, pwm_percent: int) -> None:
        if not 0 <= pwm_percent <= 100:
            raise ValueError("PWM percent must be between 0 and 100")
        response = self.send_command(f"SET_PWM {pwm_percent}")
        if response != "OK":
            raise RuntimeError(f"Unexpected SET_PWM response: {response}")

    def get_rpm(self) -> int:
        response = self.send_command("GET_RPM")
        if not response.startswith("RPM:"):
            raise RuntimeError(f"Unexpected GET_RPM response: {response}")
        return int(response.split(":", 1)[1])

# Simulated DUT used for testing without physical hardware
# Supports fault injection (e.g., stuck fan, no tach, low tach)
class SimulatedDUT(DUTInterface):
    def __init__(self, fault_mode: str = "none", rpm_scale: float = 1.0) -> None:
        self.current_pwm = 0
        self.fault_mode = fault_mode
        self.rpm_scale = rpm_scale

    def set_pwm(self, pwm_percent: int) -> None:
        if not 0 <= pwm_percent <= 100:
            raise ValueError("PWM percent must be between 0 and 100")
        if self.fault_mode == "set_pwm_no_ack":
            raise RuntimeError("Simulated fault: SET_PWM command not acknowledged")
        self.current_pwm = pwm_percent

    def get_rpm(self) -> int:
        if self.fault_mode == "no_tach":
            raise RuntimeError("Simulated fault: no tachometer response")
        if self.fault_mode == "stuck_fan":
            return 0

        ideal_rpm = {
            20: 1800,
            40: 3200,
            60: 4600,
            80: 5900,
        }.get(self.current_pwm, int(self.current_pwm * 75))

        measured = int(ideal_rpm * self.rpm_scale)

        if self.fault_mode == "tach_low":
            measured = int(measured * 0.75)
        elif self.fault_mode == "tach_high":
            measured = int(measured * 1.25)

        return measured


def rpm_in_tolerance(measured: int, expected: int, tolerance_percent: float) -> bool:
    lower = expected * (1.0 - tolerance_percent / 100.0)
    upper = expected * (1.0 + tolerance_percent / 100.0)
    return lower <= measured <= upper

# Main test loop: applies PWM setpoints, reads RPM, and validates against expected behavior
def run_test(
    dut: DUTInterface,
    points: list[TestPoint],
    settle_time_s: float,
    csv_path: Path,
) -> int:
    failures = 0
    # Log test results to CSV for traceability and post-analysis
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "timestamp",
                "pwm_percent",
                "expected_rpm",
                "measured_rpm",
                "tolerance_percent",
                "pass_fail",
                "notes",
            ]
        )
        # Execute one test point: apply PWM, measure RPM, evaluate pass/fail
        for point in points:
            print(f"\nApplying PWM={point.pwm_percent}%")
            notes = ""
            measured: Optional[int] = None
            verdict = "FAIL"

            try:
                dut.set_pwm(point.pwm_percent)
                print(f"Waiting {settle_time_s:.1f}s for fan to settle...")
                time.sleep(settle_time_s)
                measured = dut.get_rpm()
                passed = rpm_in_tolerance(
                    measured=measured,
                    expected=point.expected_rpm,
                    tolerance_percent=point.tolerance_percent,
                )
                verdict = "PASS" if passed else "FAIL"
                print(
                    f"Expected {point.expected_rpm} RPM, measured {measured} RPM "
                    f"(±{point.tolerance_percent:.1f}%) -> {verdict}"
                )
                if not passed:
                    failures += 1
                    notes = "RPM outside tolerance"
            # Capture and log errors per test point without stopping the entire test run
            except Exception as exc:
                failures += 1
                notes = str(exc)
                print(f"Test error: {notes}")

            writer.writerow(
                [
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    point.pwm_percent,
                    point.expected_rpm,
                    "" if measured is None else measured,
                    point.tolerance_percent,
                    verdict,
                    notes,
                ]
            )

    return failures


def build_default_points() -> list[TestPoint]:
    return [
        TestPoint(pwm_percent=20, expected_rpm=1800, tolerance_percent=12.0),
        TestPoint(pwm_percent=40, expected_rpm=3200, tolerance_percent=10.0),
        TestPoint(pwm_percent=60, expected_rpm=4600, tolerance_percent=10.0),
        TestPoint(pwm_percent=80, expected_rpm=5900, tolerance_percent=8.0),
    ]


def parse_args() -> argparse.Namespace:
    # Define CLI arguments to configure test execution (simulation mode, output file, serial settings)
    parser = argparse.ArgumentParser(
        description="Validate tachometer RPM against PWM command on a DUT."
    )
    parser.add_argument("--port", help="Serial port, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate")
    parser.add_argument(
        "--settle-time",
        type=float,
        default=2.0,
        help="Seconds to wait after changing PWM before reading RPM",
    )
    parser.add_argument(
        "--csv",
        default="pwm_rpm_results.csv",
        help="Path to output CSV log file",
    )
    parser.add_argument(
        "--simulate-fault",
        choices=["none", "stuck_fan", "no_tach", "tach_low", "tach_high", "set_pwm_no_ack"],
        default="none",
        help="Run without hardware and simulate a fault mode",
    )
    parser.add_argument(
        "--rpm-scale",
        type=float,
        default=1.0,
        help="Scale factor for simulated RPM in dry-run mode",
    )
    return parser.parse_args()

# Factory function to create either a real DUT or a simulated DUT based on user input
def make_dut(args: argparse.Namespace) -> DUTInterface:
    if args.simulate_fault != "none":
        print(f"Running in simulated mode with fault='{args.simulate_fault}'")
        return SimulatedDUT(fault_mode=args.simulate_fault, rpm_scale=args.rpm_scale)

    if not args.port:
        print("Running in simulated mode with no faults.")
        return SimulatedDUT(fault_mode="none")

    return SerialDUT(port=args.port, baudrate=args.baudrate)


def main() -> int:
    args = parse_args()
    #print(f"DEBUG: simulate_fault={args.simulate_fault}")
    points = build_default_points()
    csv_path = Path(args.csv)

    dut = make_dut(args)
    try:
        failures = run_test(
            dut=dut,
            points=points,
            settle_time_s=args.settle_time,
            csv_path=csv_path,
        )
    finally:
        dut.close()

    if failures:
        print(f"\nTest completed with {failures} failing point(s).")
        return 1

    print("\nAll test points passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

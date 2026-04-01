# Thermal Control System Validation Framework

## Overview

This project demonstrates a validation strategy and test framework for an embedded thermal control system.

The system under test consists of:
- MCU controlling a PWM fan
- Temperature sensor (I2C)
- Tachometer feedback for fan speed measurement

The firmware is expected to regulate temperature by dynamically adjusting fan speed.
This repository focuses on validating that behavior at system level.

## Repository Contents

- thermal_control_test_script.py
- results_nominal.csv
- results_stuck_fan.csv
- Omid_QA_Wearable_IoT_Submission.pdf

## Requirements

- Python 3.14.2
- No external libraries required

## How to Run (Windows PowerShell)

Navigate to the project folder:

```powershell
cd "C:\path\to\your\folder"
```

Run nominal validation:

```powershell
python .\thermal_control_test_script.py --simulate-fault none --csv results_nominal.csv
```

Run fault simulation for a stuck fan condition:

```powershell
python .\thermal_control_test_script.py --simulate-fault stuck_fan --csv results_stuck_fan.csv
```

## Output

The script generates CSV output in the following format:

```csv
timestamp,pwm_percent,expected_rpm,measured_rpm,pass_fail
```

## CI/CD Concept

A simple automated validation step can be integrated into a firmware pipeline:

1. Build firmware
2. Flash the device under test
3. Run the validation script
4. Collect CSV results
5. Fail the pipeline if RPM tolerance is not met or communication fails

## Notes

This repository focuses on:
- test strategy
- validation logic
- PWM-to-RPM correlation
- fault simulation
- automation readiness

## Author

Omid Madani

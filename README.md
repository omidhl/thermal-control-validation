# Thermal Control System Validation Framework

## Overview

This project demonstrates a validation strategy and test framework for
an embedded thermal control system.

The system under test consists of: - MCU controlling a PWM fan -
Temperature sensor (I2C) - Tachometer feedback for fan speed measurement

The firmware is expected to regulate temperature by dynamically
adjusting fan speed.\
This repository focuses on validating that behavior at system level.

## Repository Contents

-   thermal_control_test_script.py\
-   thermal_control_test_script_v2.py\
-   results_nominal.csv\
-   results_stuck_fan.csv

## Requirements

-   Python 3.x\
-   No external libraries required

## How to Run (Windows PowerShell)

Navigate to folder: cd
"C:`\path`{=tex}`\to`{=tex}`\your`{=tex}`\folder`{=tex}"

Run nominal test: python .`\thermal`{=tex}\_control_test_script_v2.py
--simulate-fault none --csv results_nominal.csv

Run fault simulation: python
.`\thermal`{=tex}\_control_test_script_v2.py --simulate-fault stuck_fan
--csv results_stuck_fan.csv

## Output

CSV format: timestamp,pwm_percent,expected_rpm,measured_rpm,pass_fail

## CI/CD Concept

-   Build firmware
-   Flash device
-   Run validation script
-   Fail pipeline if tolerance not met

## Author

Omid Madani

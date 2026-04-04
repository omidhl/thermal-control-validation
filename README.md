# Thermal Control System Validation Framework

## Author

Omid Madani

## Overview

This project demonstrates a system-level validation strategy and a Python-based test framework for an embedded thermal control system, including both real hardware interaction and simulated fault injection.

The system under test consists of:
- MCU controlling a PWM fan  
- Temperature sensor (I2C)  
- Tachometer feedback for fan speed measurement  

The firmware is expected to regulate temperature by dynamically adjusting fan speed.  
This repository focuses on validating that behavior at system level.

---

## Repository Contents

### Source Code
- thermal_control_test_script.py → main validation and test execution script  

### Documentation
- README.md → project overview, setup, and usage instructions  
- Omid_Madani_QA_Thermal_Control_Test_Framework.pdf → detailed test strategy and validation approach  

### Example Test Results
- results_nominal.csv → nominal operation results  
- results_stuck_fan.csv → stuck fan fault scenario  
- results_no_tach.csv → missing tachometer signal scenario  
- results_tach_low.csv → low RPM fault scenario  

Note: Additional test scenarios can be generated using CLI options described in the README. 

---

## Requirements

- Python 3.10 or newer  
- No external libraries required for simulation mode  
- pyserial (only required for real hardware communication)

---

## How to Run (Windows PowerShell)

Navigate to the project folder:

cd "C:\path\to\your\folder"

Run nominal validation:

python .\thermal_control_test_script.py --simulate-fault none --csv results_nominal.csv

Run fault simulation (stuck fan):

python .\thermal_control_test_script.py --simulate-fault stuck_fan --csv results_stuck_fan.csv

Example for real hardware (serial connection required):

python .\thermal_control_test_script.py --port COM3 --baudrate 115200 --csv results_hw.csv

---

## Output

The script generates CSV output in the following format:

timestamp,pwm_percent,expected_rpm,measured_rpm,verdict,notes

---

## Design Decisions

- The test logic is decoupled from the hardware interface using an abstract DUT interface  
- A simulated DUT is implemented to enable testing without physical hardware  
- Fault injection modes are included to validate robustness and error handling  
- CSV logging is used for traceability and post-analysis  
- CLI arguments allow flexible test configuration and automation  

---

## CI/CD Concept

A simple automated validation step can be integrated into a firmware pipeline:

1. Build firmware  
2. Flash the device under test  
3. Run the validation script  
4. Collect CSV results  
5. Fail the pipeline if RPM tolerance is not met or communication fails  

This approach enables automated regression testing of firmware behavior without requiring manual observation.

---

## Notes

This repository focuses on:
- test strategy  
- validation logic  
- PWM-to-RPM correlation  
- fault simulation  
- automation readiness  

---

## Limitations and Future Improvements

This repository focuses on:
- No retry mechanism is implemented for communication failures (e.g., serial timeouts)
- Test points (PWM vs RPM) are currently hardcoded and not externally configurable
- No filtering or averaging is applied to RPM measurements (noise not handled)
- Limited fault injection scenarios; additional cases (e.g., intermittent faults, noisy signals) could be added 

Parts of the implementation were assisted by AI tools, while the test strategy, structure, and final validation logic were designed and reviewed by the author.
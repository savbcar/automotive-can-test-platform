# Automated CAN/ECU Regression Report

Overall result: **PASS**

| Scenario | Expected | Observed | Recovery | Result |
|---|---|---|---|---|
| healthy | none | none | yes | PASS |
| soc_overrange | BMS_SOC_IMPLAUSIBLE | BMS_SOC_IMPLAUSIBLE | yes | PASS |
| overtemperature | BMS_OVER_TEMPERATURE | BMS_OVER_TEMPERATURE | yes | PASS |
| pack_voltage_low | BMS_PACK_VOLTAGE_IMPLAUSIBLE | BMS_PACK_VOLTAGE_IMPLAUSIBLE | yes | PASS |
| message_dropout | BMS_COMMUNICATION_TIMEOUT | BMS_COMMUNICATION_TIMEOUT, BMS_COUNTER_SEQUENCE | yes | PASS |
| delayed_messages | BMS_COMMUNICATION_TIMEOUT | BMS_COMMUNICATION_TIMEOUT, BMS_COUNTER_SEQUENCE | yes | PASS |
| wrong_counter | BMS_COUNTER_SEQUENCE | BMS_CHECKSUM_MISMATCH, BMS_COUNTER_SEQUENCE | yes | PASS |
| checksum_mismatch | BMS_CHECKSUM_MISMATCH | BMS_CHECKSUM_MISMATCH | yes | PASS |
| stuck_soc_injection | none | none | yes | PASS |
| noisy_temperature | none | none | yes | PASS |

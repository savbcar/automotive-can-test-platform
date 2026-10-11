# DBC Engineering Notes

`dbc/vehicle_can.dbc` is the signal-layout source of truth for the SocketCAN/cantools path.

The project intentionally distinguishes three ranges:

1. **bit-level representable range** — what can fit in the allocated bits;
2. **DBC physical range** — allowed by the signal definition;
3. **application plausibility range** — what the receiving ECU considers physically acceptable.

For fault testing, the DBC must permit some values that the application rejects. Otherwise the test infrastructure would block the invalid input before the ECU could be tested.

`cantools` is used to load and inspect the DBC and to encode/decode frames in the real adapter path. The reference codec mirrors the same layout so restricted environments can still execute tests. A parity test compares both codecs when `cantools` is installed.

# Verification Record for Packaged Repository

Verification was performed in the packaging environment before cleanup.

## Executed successfully

- Python 3.13.5 syntax compilation of `src/` and `tests/`.
- `pytest`: 39 passed, 2 intentionally skipped after the C++ build was available.
- Skipped test: `cantools` vs reference-codec parity, because `cantools` was not preinstalled and the environment had no network access to PyPI.
- CMake 3.31.6 configure/build with G++ 14.2.0.
- CTest: 1/1 C++ fault-monitor test passed.
- Python integration test invoking the compiled `fault_monitor_cli`: passed.
- Deterministic regression: 10/10 scenarios passed.
- Example JSON, CSV, Markdown and PNG report artifacts generated.
- CLI `demo`: passed.
- CLI `uds-demo`: passed.

## Not executable in the packaging environment

- `cantools` runtime path: dependency could not be downloaded because outbound package access was unavailable.
- `python-can`/SocketCAN `vcan0` path: `python-can` was not preinstalled and could not be downloaded.
- Docker build: Docker CLI/daemon was not available in the packaging environment.
- Ruff/mypy commands: tools were not preinstalled and could not be downloaded. They are configured as development dependencies/CI checks where applicable.

GitHub Actions is configured to install the dependencies and exercise the real `vcan0` path on Ubuntu. This record deliberately distinguishes executed verification from configured-but-unexecuted verification.

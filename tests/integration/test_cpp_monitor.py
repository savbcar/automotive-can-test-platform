from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "cpp" / "build" / "fault_monitor_cli"


@pytest.mark.skipif(not CLI.exists(), reason="C++ monitor has not been built")
def test_cpp_cli_flags_soc_implausibility() -> None:
    result = subprocess.run(
        [str(CLI), "110", "400", "35", "0", "1", "0.0"],
        check=True,
        capture_output=True,
        text=True,
    )
    mask = int(result.stdout.strip())
    assert mask & 0x01

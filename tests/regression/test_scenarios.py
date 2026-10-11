from pathlib import Path

import pytest

from automotive_can.config import load_simulation_config
from automotive_can.simulation import load_scenarios, run_scenario

ROOT = Path(__file__).resolve().parents[2]
CONFIG = load_simulation_config(ROOT / "configs" / "simulation.yaml")
SCENARIOS = load_scenarios(ROOT / "configs" / "regression.yaml")


@pytest.mark.parametrize("spec", SCENARIOS, ids=[item["name"] for item in SCENARIOS])
def test_regression_scenario(spec: dict[str, object]) -> None:
    result = run_scenario(spec, CONFIG)
    assert result.passed, result.summary()

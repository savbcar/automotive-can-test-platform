from __future__ import annotations

import csv
import json
from pathlib import Path

from .simulation import ScenarioResult, row_to_dict


def write_reports(results: list[ScenarioResult], output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary_json = out / "regression_summary.json"
    summary_json.write_text(
        json.dumps(
            {
                "passed": all(result.passed for result in results),
                "scenario_count": len(results),
                "results": [result.summary() for result in results],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    csv_path = out / "regression_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scenario", "passed", "expected_warning", "observed_warnings", "recovered"])
        for result in results:
            writer.writerow(
                [
                    result.name,
                    result.passed,
                    result.expected_warning or "",
                    ";".join(sorted(result.observed_warnings)),
                    result.recovered,
                ]
            )

    markdown = out / "regression_report.md"
    lines = [
        "# Automated CAN/ECU Regression Report",
        "",
        f"Overall result: **{'PASS' if all(r.passed for r in results) else 'FAIL'}**",
        "",
        "| Scenario | Expected | Observed | Recovery | Result |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| {name} | {expected} | {observed} | {recovered} | {passed} |".format(
                name=result.name,
                expected=result.expected_warning or "none",
                observed=", ".join(sorted(result.observed_warnings)) or "none",
                recovered="yes" if result.recovered else "no",
                passed="PASS" if result.passed else "FAIL",
            )
        )
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")

    traces = out / "traces"
    traces.mkdir(exist_ok=True)
    for result in results:
        path = traces / f"{result.name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            if not result.rows:
                continue
            writer = csv.DictWriter(handle, fieldnames=list(row_to_dict(result.rows[0]).keys()))
            writer.writeheader()
            writer.writerows(row_to_dict(row) for row in result.rows)

    plot_paths = _write_plots(results, out)
    return {
        "summary_json": summary_json,
        "results_csv": csv_path,
        "markdown": markdown,
        **plot_paths,
    }


def _write_plots(results: list[ScenarioResult], out: Path) -> dict[str, Path]:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return {}

    target = next((r for r in results if r.name == "soc_overrange"), results[0])
    times = [row.time_s for row in target.rows]
    tx_soc = [row.tx_soc for row in target.rows]
    rx_soc = [float("nan") if row.rx_soc is None else row.rx_soc for row in target.rows]
    fig = plt.figure(figsize=(9, 4.5))
    ax = fig.add_subplot(111)
    ax.plot(times, tx_soc, label="BMS source SOC")
    ax.plot(times, rx_soc, label="Vehicle received SOC")
    ax.axhline(100.0, linestyle="--", label="Plausibility limit")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("SOC [%]")
    ax.set_title(f"SOC trace — {target.name}")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    soc_path = out / "soc_trace.png"
    fig.savefig(soc_path, dpi=150)
    plt.close(fig)

    target_temp = next((r for r in results if r.name == "overtemperature"), results[0])
    times = [row.time_s for row in target_temp.rows]
    rx_temp = [float("nan") if row.rx_temp_c is None else row.rx_temp_c for row in target_temp.rows]
    fig = plt.figure(figsize=(9, 4.5))
    ax = fig.add_subplot(111)
    ax.plot(times, rx_temp, label="Vehicle received Tmax")
    ax.axhline(60.0, linestyle="--", label="Warning threshold")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Temperature [°C]")
    ax.set_title(f"Temperature fault trace — {target_temp.name}")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    temp_path = out / "temperature_trace.png"
    fig.savefig(temp_path, dpi=150)
    plt.close(fig)

    names = [r.name for r in results]
    counts = [len(r.observed_warnings) for r in results]
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    ax.bar(names, counts)
    ax.set_xlabel("Regression scenario")
    ax.set_ylabel("Distinct warnings observed")
    ax.set_title("Fault detection coverage evidence")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    coverage_path = out / "fault_detection_summary.png"
    fig.savefig(coverage_path, dpi=150)
    plt.close(fig)

    return {"soc_plot": soc_path, "temperature_plot": temp_path, "coverage_plot": coverage_path}

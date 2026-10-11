from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .can.socketcan import SocketCanEndpoint
from .config import load_simulation_config
from .dbc_codec import BMS_STATUS_ID, CantoolsDbcCodec, ReferenceDbcCodec
from .diagnostics.transport import DiagnosticCanServer, pack_single_frame, unpack_single_frame
from .diagnostics.uds import EducationalUdsServer
from .ecus.bms import BmsEcu
from .ecus.vehicle import VehicleControlEcu
from .reporting import write_reports
from .simulation import load_scenarios, run_scenario


def _repo_root() -> Path:
    """Locate repository assets when running from source or an installed package."""
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parents[2],
        Path("/app"),
    ]

    for candidate in candidates:
        if (
            (candidate / "configs" / "simulation.yaml").is_file()
            and (candidate / "configs" / "regression.yaml").is_file()
            and (candidate / "dbc" / "vehicle_can.dbc").is_file()
        ):
            return candidate

    return Path.cwd()


def command_demo(_: argparse.Namespace) -> int:
    codec = ReferenceDbcCodec()
    bms = BmsEcu(codec)
    vehicle = VehicleControlEcu(codec)
    frame = bms.build_status_frame()
    health = vehicle.process_frame(frame, 0.0)
    decoded = codec.decode_bms_status(frame)
    print(f"TX 0x{frame.arbitration_id:03X} {frame.data.hex(' ')}")
    print(json.dumps(decoded, indent=2, sort_keys=True))
    print(json.dumps({"healthy": health.healthy, "warnings": health.warnings}, indent=2))
    return 0 if health.healthy else 1


def command_regression(args: argparse.Namespace) -> int:
    config = load_simulation_config(args.config)
    specs = load_scenarios(args.scenarios)
    results = [run_scenario(spec, config) for spec in specs]
    paths = write_reports(results, args.output)
    for result in results:
        print(
            f"{'PASS' if result.passed else 'FAIL'} {result.name}: "
            f"expected={result.expected_warning or 'none'} "
            f"observed={sorted(result.observed_warnings)} recovered={result.recovered}"
        )
    print("Artifacts:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    return 0 if all(result.passed for result in results) else 2


def command_inspect_dbc(args: argparse.Namespace) -> int:
    dbc_path = Path(args.dbc)
    if args.backend == "cantools":
        try:
            codec = CantoolsDbcCodec(dbc_path)
        except Exception as exc:
            print(f"cantools backend unavailable: {exc}", file=sys.stderr)
            return 2
        for message in codec.db.messages:
            print(f"0x{message.frame_id:03X} {message.name} dlc={message.length}")
            for signal in message.signals:
                print(
                    f"  {signal.name}: start={signal.start} length={signal.length} "
                    f"scale={signal.scale} offset={signal.offset} unit={signal.unit}"
                )
        return 0

    print(dbc_path.read_text(encoding="utf-8"))
    return 0


def command_uds_demo(_: argparse.Namespace) -> int:
    codec = ReferenceDbcCodec()
    vehicle = VehicleControlEcu(codec)
    vehicle.process_frame(codec.encode_bms_status({
        "SOC": 82.5,
        "PackVoltage": 400.2,
        "PackCurrent": -42.3,
        "MaxCellTemp": 31.0,
        "BatteryState": 1,
        "FaultFlags": 0,
        "Counter": 0,
    }), 0.0)

    def did_soc() -> bytes:
        value = int(round((vehicle.snapshot.soc or 0.0) * 10))
        return value.to_bytes(2, "big")

    uds = EducationalUdsServer(vehicle.dtcs, {0xF190: did_soc})
    server = DiagnosticCanServer(uds)
    requests = [bytes([0x10, 0x03]), bytes([0x22, 0xF1, 0x90]), bytes([0x3E, 0x00])]
    for payload in requests:
        req = pack_single_frame(0x700, payload)
        resp = server.handle_frame(req)
        assert resp is not None
        print(f"REQ {payload.hex(' ')} -> RESP {unpack_single_frame(resp).hex(' ')}")
    return 0


def command_socketcan_demo(args: argparse.Namespace) -> int:
    dbc_path = Path(args.dbc)
    try:
        codec = CantoolsDbcCodec(dbc_path)
        bms_bus = SocketCanEndpoint(args.channel)
        vehicle_bus = SocketCanEndpoint(args.channel)
    except Exception as exc:
        print(f"SocketCAN demo unavailable: {exc}", file=sys.stderr)
        return 2

    bms = BmsEcu(codec)
    vehicle = VehicleControlEcu(codec)
    period_s = args.period_ms / 1000.0
    try:
        for i in range(args.cycles):
            now = time.monotonic()
            bms.update_synthetic_plant(i * period_s)
            frame = bms.build_status_frame()
            bms_bus.send(frame)
            rx = vehicle_bus.recv(timeout_s=period_s)
            if rx is None:
                vehicle.supervise_timeouts(time.monotonic())
                print("RX timeout")
            elif rx.arbitration_id == BMS_STATUS_ID:
                health = vehicle.process_frame(rx, now)
                print(
                    f"RX 0x{rx.arbitration_id:03X} {rx.data.hex(' ')} "
                    f"SOC={vehicle.snapshot.soc:.1f}% healthy={health.healthy}"
                )
            time.sleep(period_s)
    finally:
        bms_bus.close()
        vehicle_bus.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    root = _repo_root()
    parser = argparse.ArgumentParser(description="Automotive CAN & ECU Test Automation Platform")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run one dependency-free BMS -> Vehicle message")
    demo.set_defaults(func=command_demo)

    regression = sub.add_parser("regression", help="run deterministic SIL regression scenarios")
    regression.add_argument("--config", default=str(root / "configs" / "simulation.yaml"))
    regression.add_argument("--scenarios", default=str(root / "configs" / "regression.yaml"))
    regression.add_argument("--output", default=str(root / "reports" / "latest"))
    regression.set_defaults(func=command_regression)

    dbc = sub.add_parser("inspect-dbc", help="inspect the DBC")
    dbc.add_argument("--dbc", default=str(root / "dbc" / "vehicle_can.dbc"))
    dbc.add_argument("--backend", choices=["text", "cantools"], default="text")
    dbc.set_defaults(func=command_inspect_dbc)

    uds = sub.add_parser("uds-demo", help="run simplified diagnostic requests")
    uds.set_defaults(func=command_uds_demo)

    socketcan = sub.add_parser("socketcan-demo", help="transmit BMS_Status over Linux SocketCAN")
    socketcan.add_argument("--channel", default="vcan0")
    socketcan.add_argument("--dbc", default=str(root / "dbc" / "vehicle_can.dbc"))
    socketcan.add_argument("--cycles", type=int, default=20)
    socketcan.add_argument("--period-ms", type=int, default=100)
    socketcan.set_defaults(func=command_socketcan_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

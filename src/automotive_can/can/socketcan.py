from __future__ import annotations

from contextlib import AbstractContextManager
from types import TracebackType

from ..model import CanFrame


class SocketCanEndpoint(AbstractContextManager["SocketCanEndpoint"]):
    """Thin python-can SocketCAN adapter.

    This is the adapter used for Linux ``vcan0`` and can also target a real
    SocketCAN interface backed by supported hardware.
    """

    def __init__(self, channel: str = "vcan0") -> None:
        try:
            import can  # type: ignore
        except ImportError as exc:
            raise RuntimeError("python-can is required for SocketCAN mode") from exc
        self._can = can
        self._bus = can.Bus(interface="socketcan", channel=channel)

    def send(self, frame: CanFrame, timeout_s: float = 0.1) -> None:
        msg = self._can.Message(
            arbitration_id=frame.arbitration_id,
            data=frame.data,
            is_extended_id=frame.is_extended_id,
        )
        self._bus.send(msg, timeout=timeout_s)

    def recv(self, timeout_s: float = 0.1) -> CanFrame | None:
        msg = self._bus.recv(timeout=timeout_s)
        if msg is None:
            return None
        return CanFrame(
            arbitration_id=int(msg.arbitration_id),
            data=bytes(msg.data),
            timestamp_s=float(msg.timestamp),
            is_extended_id=bool(msg.is_extended_id),
        )

    def close(self) -> None:
        self._bus.shutdown()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

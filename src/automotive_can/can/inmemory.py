from __future__ import annotations

from collections import deque
from dataclasses import replace

from ..model import CanFrame


class InMemoryCanHub:
    """Small broadcast CAN hub for deterministic SIL tests."""

    def __init__(self) -> None:
        self._endpoints: dict[str, deque[CanFrame]] = {}

    def endpoint(self, name: str) -> "InMemoryCanEndpoint":
        if name in self._endpoints:
            raise ValueError(f"endpoint already exists: {name}")
        self._endpoints[name] = deque()
        return InMemoryCanEndpoint(name, self)

    def _broadcast(self, sender: str, frame: CanFrame) -> None:
        for name, queue in self._endpoints.items():
            if name != sender:
                queue.append(frame)


class InMemoryCanEndpoint:
    def __init__(self, name: str, hub: InMemoryCanHub) -> None:
        self.name = name
        self._hub = hub

    def send(self, frame: CanFrame, timestamp_s: float | None = None) -> None:
        stamped = replace(frame, timestamp_s=frame.timestamp_s if timestamp_s is None else timestamp_s)
        self._hub._broadcast(self.name, stamped)

    def recv(self) -> CanFrame | None:
        queue = self._hub._endpoints[self.name]
        return queue.popleft() if queue else None

    def drain(self) -> list[CanFrame]:
        out: list[CanFrame] = []
        while (frame := self.recv()) is not None:
            out.append(frame)
        return out

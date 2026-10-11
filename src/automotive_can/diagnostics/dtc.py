from __future__ import annotations

from dataclasses import replace

from ..model import Dtc


class DtcStore:
    def __init__(self) -> None:
        self._dtcs: dict[int, Dtc] = {}

    def set(self, code: int, name: str, description: str, timestamp_s: float) -> None:
        current = self._dtcs.get(code)
        if current is None:
            self._dtcs[code] = Dtc(
                code=code,
                name=name,
                description=description,
                active=True,
                occurrence_count=1,
                first_seen_s=timestamp_s,
                last_seen_s=timestamp_s,
            )
            return
        if not current.active:
            current.occurrence_count += 1
        current.active = True
        current.last_seen_s = timestamp_s

    def clear_active(self, code: int) -> None:
        if code in self._dtcs:
            self._dtcs[code].active = False

    def clear_all(self) -> None:
        self._dtcs.clear()

    def active(self) -> tuple[Dtc, ...]:
        return tuple(replace(dtc) for dtc in self._dtcs.values() if dtc.active)

    def all(self) -> tuple[Dtc, ...]:
        return tuple(replace(dtc) for dtc in self._dtcs.values())

    def codes(self, active_only: bool = True) -> tuple[int, ...]:
        source = self.active() if active_only else self.all()
        return tuple(sorted(d.code for d in source))

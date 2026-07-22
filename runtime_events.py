"""Small in-memory telemetry store shared by the bot, Web UI, and terminal."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from time import monotonic
from typing import Any


EVENT_LABELS = {
    "system": "System",
    "state_changed": "State",
    "brawler_selected": "Action",
    "match_started": "Match",
    "match_finished": "Match",
    "warning": "Warning",
    "error": "Error",
}


class RuntimeTelemetry:
    """Keep a bounded, JSON-safe picture of the current IrisAI session."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: deque[dict[str, Any]] = deque(maxlen=300)
        self._matches: deque[dict[str, Any]] = deque(maxlen=10)
        self._session_started_at: str | None = None
        self._session_started_tick: float | None = None
        self._session = self._empty_session()
        self._run = self._empty_run()
        self._logging = self._empty_logging()

    @staticmethod
    def _empty_session() -> dict[str, int]:
        return {"matches": 0, "wins": 0, "losses": 0, "trophy_delta": 0}

    @staticmethod
    def _empty_run() -> dict[str, Any]:
        return {
            "bot_status": "Stopped",
            "emulator_status": "Waiting",
            "current_state": "Unknown",
            "brawler": None,
            "trophies": None,
            "win_streak": 0,
            "playstyle": None,
            "last_result": None,
            "ips": None,
        }

    @staticmethod
    def _empty_logging() -> dict[str, Any]:
        return {
            "enabled": False,
            "path": None,
            "status": "off",
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def start_session(self) -> None:
        with self._lock:
            self._events.clear()
            self._matches.clear()
            self._session = self._empty_session()
            self._run = self._empty_run()
            self._run["bot_status"] = "Starting"
            self._session_started_at = self._now()
            self._session_started_tick = monotonic()
        self.emit("system", "Runtime start requested.")

    def update_run(self, **changes: Any) -> None:
        allowed = set(self._empty_run())
        with self._lock:
            self._run.update({key: value for key, value in changes.items() if key in allowed})

    def configure_logging(self, *, enabled: bool, path: str | None = None, status: str | None = None) -> None:
        with self._lock:
            self._logging = {
                "enabled": bool(enabled),
                "path": str(path) if path else None,
                "status": status or ("recording" if enabled else "off"),
            }

    def emit(self, event_type: str, message: str, *, details: str | None = None) -> None:
        event = {
            "timestamp": self._now(),
            "type": event_type,
            "label": EVENT_LABELS.get(event_type, "System"),
            "message": str(message).strip(),
            "details": str(details).strip() if details else "",
        }
        with self._lock:
            self._events.append(event)

    def record_match(
        self,
        *,
        brawler: str,
        result: str,
        trophy_delta: int,
        trophies: int | None,
        win_streak: int,
        playstyle: str | None = None,
        mode: str | None = None,
    ) -> None:
        result_text = str(result).strip().lower() or "unknown"
        match = {
            "timestamp": self._now(),
            "brawler": brawler or "Unknown brawler",
            "result": result_text,
            "trophy_delta": int(trophy_delta or 0),
            "trophies": trophies,
            "win_streak": int(win_streak or 0),
            "playstyle": playstyle or "",
            "mode": mode or "",
        }
        with self._lock:
            self._matches.append(match)
            self._session["matches"] += 1
            self._session["trophy_delta"] += match["trophy_delta"]
            if result_text == "victory":
                self._session["wins"] += 1
            elif result_text == "defeat":
                self._session["losses"] += 1
            self._run.update({
                "last_result": result_text,
                "brawler": match["brawler"],
                "trophies": trophies,
                "win_streak": match["win_streak"],
                "playstyle": match["playstyle"] or self._run["playstyle"],
            })

        delta_text = f"{match['trophy_delta']:+d} trophies" if match["trophy_delta"] else "no trophy change"
        self.emit("match_finished", f"{result_text.title()} with {match['brawler']} ({delta_text}).")

    def snapshot(self, *, event_limit: int = 10, debug_limit: int = 100) -> dict[str, Any]:
        with self._lock:
            duration_seconds = 0
            if self._session_started_tick is not None:
                duration_seconds = max(0, int(monotonic() - self._session_started_tick))
            events = list(reversed(self._events))
            return {
                "current_run": deepcopy(self._run),
                "session": {
                    **deepcopy(self._session),
                    "started_at": self._session_started_at,
                    "duration_seconds": duration_seconds,
                },
                "recent_events": deepcopy(events[:event_limit]),
                "debug_events": deepcopy(events[:debug_limit]),
                "recent_matches": deepcopy(list(reversed(self._matches))),
                "logging": deepcopy(self._logging),
            }


_runtime_telemetry = RuntimeTelemetry()


def get_runtime_telemetry() -> RuntimeTelemetry:
    return _runtime_telemetry

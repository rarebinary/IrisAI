import atexit
import json
import os
import platform
import shutil
import sys
import threading
from datetime import datetime
from runtime_paths import runtime_path

LOG_DIR = "logs"


class Style:
    CYAN = "\033[38;2;0;200;255m"
    WHITE = "\033[38;2;255;255;255m"
    GRAY = "\033[38;2;150;150;150m"
    GREEN = "\033[38;2;100;255;100m"
    RED = "\033[38;2;255;80;80m"
    YELLOW = "\033[38;2;255;200;50m"
    MAGENTA = "\033[38;2;200;100;255m"
    BLUE = "\033[38;2;80;150;255m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[K"


_ANSI_RE = __import__("re").compile(r"\033\[[0-9;]*[a-zA-Z]")


def _vwidth(s):
    return _ANSI_RE.sub("", s).__len__()


def _term_width():
    return shutil.get_terminal_size().columns


_figlet_cache = {}

def _figlet(text, font):
    key = (text, font)
    if key not in _figlet_cache:
        try:
            import pyfiglet
            _figlet_cache[key] = pyfiglet.figlet_format(text, font=font)
        except ImportError:
            _figlet_cache[key] = ""
    return _figlet_cache[key]


def _box(banner, inner_lines, border_color=Style.CYAN, pad=3, colorizer=None):
    lines = banner.rstrip("\n").split("\n")
    max_w = max((_vwidth(l) for l in lines), default=20)
    avail = _term_width() - 4
    if max_w + pad * 2 + 2 > avail:
        max_w = avail - pad * 2 - 2
        if max_w < 10:
            return ""
        wrapped = []
        for line in lines:
            wrapped.append(line[:_vwidth(line[:max_w])])
        lines = wrapped
    inner_w = max_w + pad * 2
    C, W, B, G, D, R = border_color, Style.WHITE, Style.BOLD, Style.GRAY, Style.DIM, Style.RESET
    out = [f"{C}▐{'▀' * inner_w}▌{R}"]
    out.append(f"{C}▐{' ' * inner_w}▌{R}")
    for line in lines:
        vw = _vwidth(line)
        if vw > max_w:
            line = line[:max_w]
            vw = max_w
        if colorizer:
            colored = colorizer(line)
            cvw = _vwidth(colored)
            out.append(f"{C}▐{' ' * pad}{B}{colored}{R}{' ' * (inner_w - pad - cvw)}{C}▌{R}")
        else:
            out.append(f"{C}▐{' ' * pad}{W}{B}{line}{R}{' ' * (inner_w - pad - vw)}{C}▌{R}")
    out.append(f"{C}▐{' ' * inner_w}▌{R}")
    for item in inner_lines:
        vw = _vwidth(item)
        out.append(f"{C}▐{R}  {item}{' ' * (inner_w - 2 - vw)}{C}▌{R}")
    out.append(f"{C}▐{' ' * inner_w}▌{R}")
    out.append(f"{C}▐{'▄' * inner_w}▌{R}")
    return "\n".join(out)


def _pick_logo(avail):
    fonts = [
        ("IRIS AI", "3d-ascii", 58),
        ("IrisAI", "3d-ascii", 49),
        ("IRIS AI", "slant", 38),
        ("IRIS", "slant", 23),
        ("IrisAI", "small", 24),
    ]
    for text, font, w in fonts:
        if w + 10 <= avail:
            return _figlet(text, font)
    if avail >= 20:
        return _figlet("IRIS", "small")
    return None


def _tty():
    return getattr(sys, '__stdout__', None) or sys.stdout


IRIS_ASCII = r"""
  ___ ____  ___ ____      _    ___
 |_ _|  _ \|_ _/ ___|    / \  |_ _|
  | || |_) || |\___ \   / _ \  | |
  | ||  _ < | | ___) | / ___ \ | |
 |___|_| \_\___|____/ /_/   \_\___|
""".strip("\n")


def print_crash_banner():
    avail = _term_width()
    banner = _pick_logo(avail)
    if not banner:
        _tty().write(f"\n{Style.RED}{Style.BOLD}ERROR{Style.RESET}  {Style.YELLOW}check logs/{Style.RESET}\n\n")
        _tty().flush()
        return
    box = _box(banner, [
        f"{Style.YELLOW}check logs/{Style.RESET}",
    ], border_color=Style.RED)
    _tty().write("\n" + box + "\n" if box else f"\n{Style.RED}{Style.BOLD}ERROR{Style.RESET}  {Style.YELLOW}check logs/{Style.RESET}\n\n")
    _tty().flush()


class _CapturedStream:
    def __init__(self, capture, stream, stream_name):
        self.capture = capture
        self.stream = stream
        self.stream_name = stream_name

    def write(self, text):
        self.capture.write(text, self.stream, self.stream_name)

    def flush(self):
        self.capture.flush(self.stream)

    def isatty(self):
        return bool(self.capture.debug and self.stream.isatty())

    @property
    def encoding(self):
        return getattr(self.stream, "encoding", "utf-8")


class SessionLogCapture:
    """Capture technical output and finish it with a shareable session summary."""

    def __init__(self, *, enabled=False, debug=False, version="local"):
        self.enabled = bool(enabled)
        self.debug = bool(debug)
        self.version = version
        self.started_at = datetime.now()
        self.path = None
        self._file = None
        self._closed = False
        self._lock = threading.RLock()
        self._stdout = sys.__stdout__
        self._stderr = sys.__stderr__

        if self.enabled:
            timestamp = self.started_at.strftime("%Y-%m-%d_%H-%M-%S")
            self.path = runtime_path(LOG_DIR, f"iris-session_{timestamp}_{os.getpid()}.log").resolve()
            self._file = open(self.path, "x", encoding="utf-8", buffering=1)
            self._write_header()

        self.stdout_proxy = _CapturedStream(self, self._stdout, "stdout")
        self.stderr_proxy = _CapturedStream(self, self._stderr, "stderr")
        sys.stdout = self.stdout_proxy
        sys.stderr = self.stderr_proxy
        atexit.register(self.close)

    def _write_header(self):
        metadata = {
            "started_at": self.started_at.isoformat(),
            "iris_version": self.version,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pid": os.getpid(),
            "runtime_dir": str(self.path.parent.parent),
            "mode": "debug" if self.debug else "log",
        }
        self._file.write("=== IrisAI diagnostic session ===\n")
        for key, value in metadata.items():
            self._file.write(f"{key}: {value}\n")
        self._file.write("=== Technical output ===\n")

    def write(self, text, original_stream, stream_name):
        if not text:
            return 0
        original_length = len(text)
        if isinstance(text, bytes):
            encoding = getattr(original_stream, "encoding", None) or "utf-8"
            text = text.decode(encoding, errors="replace")
        elif not isinstance(text, str):
            text = str(text)
        with self._lock:
            if self._file and not self._closed:
                if stream_name == "stderr" and text.strip():
                    self._file.write("[stderr] ")
                self._file.write(text)
            if self.debug:
                original_stream.write(text)
                original_stream.flush()
        return original_length

    def flush(self, original_stream=None):
        with self._lock:
            if self._file and not self._closed:
                self._file.flush()
            if self.debug and original_stream:
                original_stream.flush()

    def close(self, *, snapshot=None, reason="process_exit", announce=True):
        with self._lock:
            if self._closed:
                return self.path
            self._closed = True

            if sys.stdout is self.stdout_proxy:
                sys.stdout = self._stdout
            if sys.stderr is self.stderr_proxy:
                sys.stderr = self._stderr

            if self._file:
                ended_at = datetime.now()
                summary = snapshot or {}
                self._file.write("\n=== Session summary ===\n")
                self._file.write(f"ended_at: {ended_at.isoformat()}\n")
                self._file.write(f"exit_reason: {reason}\n")
                self._file.write(f"duration_seconds: {int((ended_at - self.started_at).total_seconds())}\n")
                self._file.write(json.dumps(summary, indent=2, ensure_ascii=True, default=str))
                self._file.write("\n=== End of IrisAI diagnostic session ===\n")
                self._file.flush()
                self._file.close()
                self._file = None

        try:
            atexit.unregister(self.close)
        except Exception:
            pass

        if self.path and announce:
            try:
                self._stdout.write(
                    f"\n{Style.GREEN}{Style.BOLD}Session log saved.{Style.RESET}\n"
                    f"{Style.DIM}File:{Style.RESET} {self.path}\n"
                    f"{Style.DIM}You can send this file for debugging.{Style.RESET}\n"
                )
                self._stdout.flush()
            except OSError:
                pass
        return self.path


def setup_session_logging(*, enabled=False, debug=False, version="local"):
    return SessionLogCapture(enabled=enabled, debug=debug, version=version)


def _format_duration(seconds):
    seconds = max(0, int(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _result_style(result):
    normalized = str(result or "").lower()
    if normalized == "victory":
        return Style.GREEN, "VICTORY"
    if normalized == "defeat":
        return Style.RED, "DEFEAT"
    return Style.YELLOW, normalized.upper() or "UNKNOWN"


def _clip(value, width):
    text = str(value or "-")
    return text if len(text) <= width else f"{text[:max(1, width - 1)]}…"


def render_terminal_dashboard(snapshot, *, version="local", runtime_dir=".iris_runtime", debug=False):
    """Render the calm, fixed terminal view used during normal operation."""
    terminal = _tty()
    if not terminal.isatty():
        return

    run = snapshot.get("current_run", {})
    session = snapshot.get("session", {})
    logging_status = snapshot.get("logging", {})
    events = snapshot.get("debug_events" if debug else "recent_events", [])
    matches = snapshot.get("recent_matches", [])
    width = max(56, min(_term_width() - 2, 104))
    rule = "─" * width
    def row(label, value):
        return f"{Style.DIM}{label:<15}{Style.RESET}{_clip(value, width - 15)}"

    lines = [
        Style.CYAN + IRIS_ASCII + Style.RESET,
        f"{Style.DIM}IrisAI {version}  •  {runtime_dir}  •  {'DEBUG' if debug else 'NORMAL'}{Style.RESET}",
        rule,
        f"{Style.BOLD}SYSTEM{Style.RESET}",
        row("Bot", run.get("bot_status")),
        row("Emulator", run.get("emulator_status")),
        row("State", run.get("current_state")),
        row("Session log", logging_status.get("path") if logging_status.get("enabled") else "Off (use --log)"),
        rule,
        f"{Style.BOLD}CURRENT RUN{Style.RESET}",
        row("Brawler", run.get("brawler")),
        row("Trophies", run.get("trophies")),
        row("Win streak", run.get("win_streak", 0)),
        row("Playstyle", run.get("playstyle")),
        row("Session", f"{_format_duration(session.get('duration_seconds'))}  {session.get('wins', 0)}W / {session.get('losses', 0)}L  {session.get('trophy_delta', 0):+d} trophies"),
        rule,
        f"{Style.BOLD}LAST MATCHES{Style.RESET}",
    ]

    if matches:
        for match in matches[:10]:
            color, result = _result_style(match.get("result"))
            detail = f"{_clip(match.get('brawler'), 18):<18} {match.get('trophy_delta', 0):+d} trophies"
            lines.append(f"{color}{result:<8}{Style.RESET} {detail}")
    else:
        lines.append(f"{Style.DIM}No matches recorded in this session.{Style.RESET}")

    lines.extend([rule, f"{Style.BOLD}{'DEBUG LOGS' if debug else 'RECENT EVENTS'}{Style.RESET}"])
    if events:
        for event in events[:10]:
            label = _clip(event.get("label"), 9).upper()
            message = _clip(event.get("details") if debug and event.get("details") else event.get("message"), width - 13)
            lines.append(f"{Style.DIM}{label:<10}{Style.RESET} {message}")
    else:
        lines.append(f"{Style.DIM}Waiting for an event.{Style.RESET}")

    terminal.write("\033[H\033[2J" + "\n".join(lines) + "\n")
    terminal.flush()

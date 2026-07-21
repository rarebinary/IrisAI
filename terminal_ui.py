import os
import sys
import time
from datetime import datetime

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


def _figlet(text, font):
    try:
        import pyfiglet
        return pyfiglet.figlet_format(text, font=font)
    except ImportError:
        return text + "\n"


def _box(banner, inner_lines, border_color=Style.CYAN):
    lines = banner.rstrip("\n").split("\n")
    max_w = max((_vwidth(l) for l in lines), default=40)
    inner_w = max_w + 6
    C, W, B, G, D, R = border_color, Style.WHITE, Style.BOLD, Style.GRAY, Style.DIM, Style.RESET

    out = [f"{C}╔{'═' * inner_w}╗{R}"]
    out.append(f"{C}║{' ' * inner_w}║{R}")
    for line in lines:
        out.append(f"{C}║   {W}{B}{line}{R}{' ' * (inner_w - 3 - _vwidth(line))}{C}║{R}")
    out.append(f"{C}║{' ' * inner_w}║{R}")
    for item in inner_lines:
        out.append(f"{C}║{R}  {item}{' ' * (inner_w - 2 - _vwidth(item))}{C}║{R}")
    out.append(f"{C}║{' ' * inner_w}║{R}")
    out.append(f"{C}╚{'═' * inner_w}╝{R}")
    return "\n".join(out)


def print_splash():
    banner = _figlet("IRIS AI", "slant")
    print()
    print(_box(banner, [
        f"{Style.GRAY}Brawl Stars Automation Bot{Style.RESET}          {Style.GRAY}v2.0.0{Style.RESET}",
        f"{Style.DIM}github.com/rarebinary/IrisAI{Style.RESET}",
    ]))
    print()


def print_crash_banner():
    banner = _figlet("CRASH", "doom")
    print()
    print(_box(banner, [
        f"{Style.YELLOW}Check logs/ for details{Style.RESET}",
    ], border_color=Style.RED))
    print()


def setup_session_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(LOG_DIR, f"session_{ts}.log")
    log_file = open(log_path, "a", encoding="utf-8")

    log_file.write(f"--- IrisAI session started at {datetime.now().isoformat()} ---\n")
    log_file.flush()

    class Tee:
        def write(self_, text):
            sys.__stdout__.write(text)
            sys.__stdout__.flush()
            log_file.write(text)
            log_file.flush()

        def flush(self_):
            sys.__stdout__.flush()
            log_file.flush()

    sys.stdout = Tee()
    sys.stderr = Tee()
    return log_path


def build_status_line(ips, brawler, state, trophies, playstyle, session_time, wins=None, win_streak=None):
    parts = [
        f"{Style.CYAN}{ips:.1f}{Style.DIM} IPS{Style.RESET}",
        f"{Style.WHITE}{brawler}{Style.RESET}",
    ]
    if wins is not None:
        parts.append(f"{Style.GREEN}✔ {wins}{Style.RESET}")
    if state:
        state_color = Style.GREEN if state == "match" else Style.YELLOW
        parts.append(f"{state_color}{state}{Style.RESET}")
    parts.append(f"{Style.MAGENTA}♥ {trophies}{Style.RESET}")
    if win_streak is not None and win_streak:
        parts.append(f"{Style.BLUE}🔥 {win_streak}{Style.RESET}")
    parts.append(f"{Style.GRAY}{playstyle}{Style.RESET}")
    parts.append(f"{Style.DIM}⏱ {session_time}{Style.RESET}")
    return " │ ".join(parts)

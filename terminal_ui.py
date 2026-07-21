import os
import shutil
import sys
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


def _term_width():
    return shutil.get_terminal_size().columns


def _figlet(text, font):
    try:
        import pyfiglet
        return pyfiglet.figlet_format(text, font=font)
    except ImportError:
        return ""


def _box(banner, inner_lines, border_color=Style.CYAN, pad=3):
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
    out = [f"{C}╔{'─' * inner_w}╗{R}"]
    out.append(f"{C}│{' ' * inner_w}│{R}")
    for line in lines:
        vw = _vwidth(line)
        if vw > max_w:
            line = line[:max_w]
            vw = max_w
        out.append(f"{C}│{' ' * pad}{W}{B}{line}{R}{' ' * (inner_w - pad - vw)}{C}│{R}")
    out.append(f"{C}│{' ' * inner_w}│{R}")
    for item in inner_lines:
        vw = _vwidth(item)
        out.append(f"{C}│{R}  {item}{' ' * (inner_w - 2 - vw)}{C}│{R}")
    out.append(f"{C}│{' ' * inner_w}│{R}")
    out.append(f"{C}╚{'─' * inner_w}╝{R}")
    return "\n".join(out)


def _pick_logo(avail):
    fonts = [
        ("IRIS AI", "slant", 42),
        ("IRIS", "slant", 28),
        ("IRIS AI", "small", 24),
    ]
    for text, font, w in fonts:
        if w + 10 <= avail:
            return _figlet(text, font)
    return None


def print_splash():
    avail = _term_width()
    banner = _pick_logo(avail)
    if not banner:
        print(f"\n{Style.CYAN}{Style.BOLD}IRIS AI{Style.RESET}  {Style.GRAY}v2.0.0{Style.RESET}\n")
        return
    inner = [
        f"{Style.GRAY}Brawl Stars Automation Bot{Style.RESET}",
        f"{Style.DIM}github.com/rarebinary/IrisAI{Style.RESET}",
    ]
    if avail >= 60:
        inner[0] = f"{Style.GRAY}Brawl Stars Automation Bot{Style.RESET}  {Style.GRAY}v2.0.0{Style.RESET}"
    box = _box(banner, inner)
    print("\n" + box if box else f"\n{Style.CYAN}{Style.BOLD}IRIS AI{Style.RESET}  {Style.GRAY}v2.0.0{Style.RESET}\n")


def print_crash_banner():
    avail = _term_width()
    banner = _pick_logo(avail)
    if not banner:
        print(f"\n{Style.RED}{Style.BOLD}ERROR{Style.RESET}  {Style.YELLOW}check logs/{Style.RESET}\n")
        return
    box = _box(banner, [
        f"{Style.YELLOW}check logs/{Style.RESET}",
    ], border_color=Style.RED)
    print("\n" + box if box else f"\n{Style.RED}{Style.BOLD}ERROR{Style.RESET}  {Style.YELLOW}check logs/{Style.RESET}\n")


def setup_session_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(LOG_DIR, f"session_{ts}.log")
    log_file = open(log_path, "a", encoding="utf-8")
    log_file.write(f"--- IrisAI {datetime.now().isoformat()} ---\n")
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
    avail = _term_width() - 2
    parts = [
        f"{Style.CYAN}{ips:.1f}{Style.DIM} IPS{Style.RESET}",
        f"{Style.WHITE}{brawler}{Style.RESET}",
    ]
    if wins is not None:
        parts.append(f"{Style.GREEN}{wins}W{Style.RESET}")
    if state:
        c = Style.GREEN if state == "match" else Style.YELLOW
        parts.append(f"{c}{state}{Style.RESET}")
    parts.append(f"{Style.MAGENTA}{trophies}t{Style.RESET}")
    if win_streak:
        parts.append(f"{Style.BLUE}s{win_streak}{Style.RESET}")
    parts.append(f"{Style.GRAY}{playstyle}{Style.RESET}")
    parts.append(f"{Style.DIM}{session_time}{Style.RESET}")

    line = " ".join(parts)
    while _vwidth(line) > avail and len(parts) > 2:
        parts.pop(-2)
        line = " ".join(parts)
    return line

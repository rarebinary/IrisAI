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


LOGO = f"""
{Style.CYAN}╔═══════════════════════════════════════════════════╗
║  {Style.WHITE}{Style.BOLD}◈   I R I S   A I   ◈{Style.RESET}{Style.CYAN}                         ║
║  {Style.GRAY}Brawl Stars Automation Bot{Style.RESET}{Style.CYAN}                          ║
║  {Style.DIM}github.com/rarebinary/IrisAI{Style.RESET}{Style.CYAN}                     ║
╚═══════════════════════════════════════════════════╝{Style.RESET}
"""

_CRASH_BANNER = f"""
{Style.RED}{Style.BOLD}╔══════════════════════════════════════════════╗
║  ✖   B O T   C R A S H E D              ║
║  {Style.YELLOW}Check logs/ for details{Style.RED}                  ║
╚══════════════════════════════════════════════╝{Style.RESET}
"""


def print_splash():
    print(LOGO)


def print_crash_banner():
    print(_CRASH_BANNER)


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

import inspect
import os
import sys

# Monkey-patch inspect.getfile to prevent Nuitka + PyTorch crash
_original_getfile = inspect.getfile
def _patched_getfile(obj):
    res = _original_getfile(obj)
    return res if res is not None else "<unknown_nuitka_file>"

inspect.getfile = _patched_getfile


if __name__ == "__main__" and len(sys.argv) >= 9 and sys.argv[1] == "--debug-viewer-worker":
    from debug_view import DEFAULT_DEBUG_VIEW_FPS, run_viewer_worker

    run_viewer_worker(
        shared_memory_name=sys.argv[2],
        debug_memory_name=sys.argv[3],
        height=int(sys.argv[4]),
        width=int(sys.argv[5]),
        channels=int(sys.argv[6]),
        dtype_text=sys.argv[7],
        title=sys.argv[8],
        clip_fps=float(sys.argv[9]) if len(sys.argv) >= 10 else DEFAULT_DEBUG_VIEW_FPS,
        record_clips=(len(sys.argv) >= 11 and sys.argv[10] == "1"),
    )
    sys.exit(0)

from adbutils import AdbError
import logging
import signal
import socket
import threading
import time
import traceback
import webbrowser
from lobby_automation import LobbyAutomation
from play import Play
from stage_manager import StageManager
from state_finder import get_state
from time_management import TimeManagement
from config_loader import get_config
from utils import load_toml_as_dict, current_wall_model_is_latest, api_base_url, load_iris_script, save_brawler_data, \
    clean_queue
from utils import get_brawler_list, update_missing_brawlers_info, check_version, notify_user, update_wall_model_classes, get_latest_wall_model_file, cprint, IRIS_VERSION
from window_controller import WindowController
from webui import create_app
from terminal_ui import setup_session_logging, print_crash_banner, render_terminal_dashboard
from runtime_events import get_runtime_telemetry
from runtime_paths import get_runtime_dir, runtime_path


DEBUG_MODE = "--debug" in sys.argv
LOG_MODE = DEBUG_MODE or "--log" in sys.argv or os.environ.get("IRIS_LOG") == "1"


def format_state_label(state):
    if not state:
        return "Unknown"
    return {
        "match_making": "Matchmaking",
    }.get(state, state.replace("_", " ").title())


def apply_play_order(queue_data):
    play_order = str(load_toml_as_dict("cfg/general_config.toml").get("play_order", "in_order")).strip().lower()
    if play_order == "lowest_to_highest":
        ordered_data = sorted(queue_data, key=lambda item: int(item.get("trophies", 0) or 0))
    elif play_order == "highest_to_lowest":
        ordered_data = sorted(queue_data, key=lambda item: int(item.get("trophies", 0) or 0), reverse=True)
    else:
        return queue_data

    for item in ordered_data:
        item["automatically_pick"] = True
    return ordered_data


def play_alarm():
    try:
        import subprocess
        subprocess.Popen(["afplay", "sounds/u_inx5oo5fv3-alarm-327234.mp3"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def iris_main(discord_bot, queue_data, stop_event=None, runtime_control=None):
    class Main:
        def __init__(self):
            self.telemetry = get_runtime_telemetry()
            current_playstyle = load_toml_as_dict("cfg/bot_config.toml").get("current_playstyle", "lane_up.iris")
            try:
                self.max_ips = int(get_config("cfg/general_config.toml", "max_ips", "auto"))
            except ValueError:
                self.max_ips = None

            if self.max_ips:
                self.window_controller = WindowController(self.max_ips)
            else:
                self.window_controller = WindowController()
            data = clean_queue(queue_data)
            data = apply_play_order(data)
            if not data:
                raise ValueError("No valid brawler data found. Please add a brawler configuration in the UI before starting the bot.")
            save_brawler_data(data)
            print("Starting with queue data:", data)
            self.playstyle_info, iris_code = load_iris_script(current_playstyle)
            self.Play = Play(*self.load_models(), self.window_controller, iris_code)
            self.Time_management = TimeManagement()
            self.lobby_automator = LobbyAutomation(self.window_controller)
            self.runtime_control = runtime_control
            self.Stage_manager = StageManager(data, self.lobby_automator, self.window_controller, self.playstyle_info, self.get_latest_state, runtime_control=runtime_control)
            self.states_requiring_data = ["lobby"]
            self.no_detections_action_threshold = 60 * 8
            self.state = None
            self.stop_event = stop_event
            self.state_lock = threading.Lock()
            self.latest_state_frame_time = 0.0
            self.max_cached_state_age = 1.0
            self.state_checker_stop_event = threading.Event()
            self.state_checker_thread = None
            self.update_trophy_observer()

            self.run_for_minutes = int(get_config("cfg/general_config.toml", "run_for_minutes", 60))
            self.webhook_ping_every_minutes = get_config("cfg/webhook_config.toml", "ping_every_x_minutes", 0)
            self.time_since_last_webhook_ping = time.time()
            self.start_time = time.time()
            self.time_to_stop = False
            self.in_cooldown = False
            self.cooldown_start_time = 0
            self.cooldown_duration = 3 * 60
            self.window_controller.screenshot()
            discord_bot.set_window_controller(self.window_controller)
            self.start_state_checker()
            print("Initialization complete, starting main loop.")
            self.picked_first_brawler = False
            self.brawler_selection_stuck_count = 0
            self.current_playstyle_name = self.playstyle_info.get("name", current_playstyle.replace(".iris", ""))
            current_brawler = self.Stage_manager.brawlers_pick_data[0] if self.Stage_manager.brawlers_pick_data else {}
            self.telemetry.update_run(
                bot_status="Running",
                emulator_status="Connected",
                brawler=current_brawler.get("brawler"),
                trophies=self.Stage_manager.Trophy_observer.current_trophies,
                win_streak=self.Stage_manager.Trophy_observer.win_streak,
                playstyle=self.current_playstyle_name,
            )
            self.telemetry.emit("system", "Emulator connected. Initializing the run.")
            self.time_since_checked_if_brawl_stars_crashed = time.time()
            self.check_if_brawl_stars_crashed_timer = get_config("cfg/time_tresholds.toml", "check_if_brawl_stars_crashed", 20)
            self.ping_when_stuck = get_config("cfg/webhook_config.toml", "ping_when_stuck", True)

        def update_trophy_observer(self):
            if not self.Stage_manager.brawlers_pick_data:
                return
            current_brawler_data = self.Stage_manager.brawlers_pick_data[0]
            self.Stage_manager.Trophy_observer.win_streak = current_brawler_data['win_streak']
            self.Stage_manager.Trophy_observer.current_trophies = current_brawler_data['trophies']
            self.Stage_manager.Trophy_observer.current_wins = current_brawler_data['wins'] if current_brawler_data['wins'] != "" else 0
            self.telemetry.update_run(
                brawler=current_brawler_data.get("brawler"),
                trophies=self.Stage_manager.Trophy_observer.current_trophies,
                win_streak=self.Stage_manager.Trophy_observer.win_streak,
            )

        @staticmethod
        def load_models():
            folder_path = "./models/"
            return [
                folder_path + 'mainInGameModel.onnx',
                folder_path + 'tileDetector.onnx',
                folder_path + 'closeTileDetector.onnx',
            ]

        def restart_brawl_stars(self):
            self.window_controller.restart_brawl_stars()
            self.time_since_checked_if_brawl_stars_crashed = time.time()
            self.Play.time_since_detections["player"] = time.time()
            self.Play.time_since_detections["enemy"] = time.time()
            if not self.window_controller.is_brawl_stars_running():
                self.telemetry.update_run(emulator_status="Disconnected")
                self.telemetry.emit("error", "Brawl Stars could not be restored after reconnecting.")
                if get_config("cfg/webhook_config.toml", "ping_when_stuck", True):
                    screenshot = self.window_controller.screenshot()
                    notify_user("bot_is_stuck", screenshot, self.Stage_manager)
                    print("Bot got stuck. User notified.")
                print("Shutting down.")
                self.window_controller.release_movement()
                self.window_controller.close()
                discord_bot.set_window_controller(None)
                if self.runtime_control:
                    self.runtime_control.request_stop()
                    self.runtime_control.mark_error("Restart BS failed")
                return

        def should_stop(self):
            return bool(self.stop_event and self.stop_event.is_set()) or bool(self.runtime_control and self.runtime_control.should_stop())

        def should_pause(self):
            return bool(self.runtime_control and self.runtime_control.should_pause())

        def sleep_interruptible(self, duration, allow_pause=True, poll_interval=0.1):
            end_time = time.time() + duration
            while time.time() < end_time:
                if self.should_stop():
                    return "stop"
                if allow_pause and self.should_pause():
                    return "pause"
                time.sleep(min(poll_interval, max(end_time - time.time(), 0)))
            return None

        def stop_gracefully(self):
            cprint("Stop requested from UI - shutting down gracefully", "#AAE5A4")
            if load_toml_as_dict("cfg/general_config.toml").get("alarm_enabled", True):
                play_alarm()
            self.stop_state_checker()
            self.Play.close()
            self.window_controller.close()
            discord_bot.set_window_controller(None)
            self.telemetry.update_run(bot_status="Stopped", emulator_status="Disconnected")
            self.telemetry.emit("system", "Runtime stopped safely.")

        def start_state_checker(self):
            if self.state_checker_thread and self.state_checker_thread.is_alive():
                return
            self.state_checker_stop_event.clear()
            self.state_checker_thread = threading.Thread(
                target=self.state_checker_loop,
                daemon=True,
                name="iris-state-checker"
            )
            self.state_checker_thread.start()

        def stop_state_checker(self):
            self.state_checker_stop_event.set()
            if self.state_checker_thread and self.state_checker_thread.is_alive():
                self.state_checker_thread.join(timeout=1.0)

        def set_latest_state(self, state):
            with self.state_lock:
                previous_state = self.state
                self.state = state
            if state and state != previous_state:
                readable_state = format_state_label(state)
                self.telemetry.update_run(current_state=readable_state)
                if state == "match":
                    self.telemetry.emit("match_started", "Match started.")
                else:
                    self.telemetry.emit("state_changed", f"State changed to {readable_state}.")

        def get_latest_state(self):
            with self.state_lock:
                return self.state

        def handle_detected_state(self, state):
            if state is None:
                return
            self.set_latest_state(state)

            logging.debug("State: %s", state)
            frame_data = None
            self.Stage_manager.do_state(state, frame_data)
            if state != "match":
                self.Play.time_since_last_proceeding = time.time()

        def state_checker_loop(self):
            last_checked_frame_time = 0.0
            while not self.state_checker_stop_event.is_set():
                frame, frame_time = self.window_controller.get_latest_frame()
                if frame is None or frame_time <= last_checked_frame_time:
                    self.state_checker_stop_event.wait(0.01)
                    continue

                last_checked_frame_time = frame_time
                try:
                    self.set_latest_state(get_state(frame))
                except Exception as e:
                    self.telemetry.emit("warning", "State checker could not read the latest frame.", details=str(e))
                    print(f"State checker failed: {e}")
                    self.state_checker_stop_event.wait(0.1)

        def wait_while_paused(self):
            if not self.runtime_control:
                return

            self.window_controller.release_movement()
            self.runtime_control.mark_paused()
            self.telemetry.update_run(bot_status="Paused")
            self.telemetry.emit("system", "Runtime paused in the lobby.")
            cprint("Iris is paused in the lobby. Waiting for Start to resume.", "#AAE5A4")

            while self.should_pause() and not self.should_stop():
                state = self.get_latest_state()
                if state is None:
                    if self.sleep_interruptible(0.25, allow_pause=False) == "stop":
                        return
                    continue
                if self.sleep_interruptible(0.75, allow_pause=False) == "stop":
                    return

            if not self.should_stop():
                self.runtime_control.mark_running()
                self.telemetry.update_run(bot_status="Running")
                self.telemetry.emit("system", "Runtime resumed.")
                self.time_since_last_webhook_ping = time.time()
                print("Pause released, resuming run.")

        def handle_pause_request(self):
            if self.should_pause() and not self.should_stop():
                cprint("Pause requested from UI - waiting", "#AAE5A4")
                self.wait_while_paused()

        def manage_time_tasks(self, frame):
            if self.Time_management.state_check():
                state = self.get_latest_state()
                if state is not None:
                    self.handle_detected_state(state)
            if self.Time_management.no_detections_check():
                frame_data = self.Play.time_since_detections
                t_now = time.time()
                for key, value in frame_data.items():
                    if t_now - value > self.no_detections_action_threshold:
                        self.restart_brawl_stars()
            if self.Time_management.idle_check():
                self.lobby_automator.check_for_idle(frame)

            current_time = time.time()
            if self.webhook_ping_every_minutes and current_time - self.time_since_last_webhook_ping >= self.webhook_ping_every_minutes * 60:
                screenshot = self.window_controller.screenshot()
                notify_user("regular_minutes_ping", screenshot, self.Stage_manager)
                self.time_since_last_webhook_ping = current_time
                print(f"Sent regular webhook ping after {self.webhook_ping_every_minutes} minutes.")

        def check_and_handle_brawl_stars_crash(self):
            c_time = time.time()
            if c_time - self.time_since_checked_if_brawl_stars_crashed > self.check_if_brawl_stars_crashed_timer:
                try:
                    opened_app = self.window_controller.device.app_current().package.strip()
                    if not self.window_controller.is_brawl_stars_running():
                        print(f"Brawl stars has crashed, {opened_app} is the app opened ! Restarting...")
                        self.window_controller.device.app_start(self.window_controller.BRAWL_STARS_PACKAGE)
                        time.sleep(3)
                        self.time_since_checked_if_brawl_stars_crashed = time.time()
                    else:
                        self.time_since_checked_if_brawl_stars_crashed = c_time
                except AdbError:
                    print("There was an error checking if Brawl Stars is running. Attempting to reconnect scrcpy...")
                    if not self.window_controller.reconnect_scrcpy():
                        print("Reconnect failed -- restarting Brawl Stars")
                        self.restart_brawl_stars()

        def main(self):
            s_time = time.time()
            c = 0
            self.time_since_last_webhook_ping = time.time()
            if self.runtime_control:
                self.runtime_control.mark_running()

            fps_timer = time.perf_counter()
            fps_counter = 0

            while True:
                if self.should_stop():
                    self.stop_gracefully()
                    break

                if self.get_latest_state() == "lobby":
                    if self.should_pause():
                        self.handle_pause_request()
                        if self.should_stop():
                            self.stop_gracefully()
                            break
                        if self.should_pause():
                            continue

                if not self.picked_first_brawler and self.get_latest_state() == "lobby":
                    if self.Stage_manager.brawlers_pick_data[0]['automatically_pick']:
                        next_brawler_name = self.Stage_manager.brawlers_pick_data[0]['brawler']
                        self.telemetry.update_run(brawler=next_brawler_name)
                        self.telemetry.emit("brawler_selected", f"Selecting {next_brawler_name}.")
                        print("Picking brawler automatically")
                        if self.runtime_control:
                            self.runtime_control.mark_running()
                        select_brawler = self.lobby_automator.select_brawler(next_brawler_name, self.get_latest_state, runtime_control=self.runtime_control)

                        while select_brawler in ["failed", "error"]:
                            print("Automatic brawler selection failed.")
                            if self.ping_when_stuck:
                                screenshot = self.window_controller.screenshot()
                                notify_user("bot_failed_brawler_selection", screenshot, self.Stage_manager)
                            failed_brawler = self.Stage_manager.brawlers_pick_data.pop(0)
                            self.Stage_manager.brawlers_pick_data.append(failed_brawler)
                            next_brawler_name = self.Stage_manager.brawlers_pick_data[0]['brawler']
                            self.telemetry.update_run(brawler=next_brawler_name)
                            self.telemetry.emit("warning", f"Trying {next_brawler_name} after a selection failure.")
                            select_brawler = self.lobby_automator.select_brawler(next_brawler_name, self.get_latest_state, runtime_control=self.runtime_control)

                        if select_brawler == "aborted" or select_brawler == "stuck":
                            self.brawler_selection_stuck_count += 1
                            if self.brawler_selection_stuck_count >= 3:
                                print("Brawler selection stuck too many times — continuing with current selection.")
                                self.picked_first_brawler = True
                            continue
                        self.picked_first_brawler = True
                        self.update_trophy_observer()
                    else:
                        self.picked_first_brawler = True

                iter_start = time.perf_counter()

                t_now = time.time()

                if self.run_for_minutes > 0 and not self.in_cooldown:
                    elapsed_time = (t_now - self.start_time) / 60
                    if elapsed_time >= self.run_for_minutes:
                        cprint(f"timer is done, {self.run_for_minutes} is over. continuing for 3 minutes if in game", "#AAE5A4")
                        self.in_cooldown = True
                        self.cooldown_start_time = t_now
                        self.Stage_manager.states['lobby'] = lambda: 0

                if self.in_cooldown and t_now - self.cooldown_start_time >= self.cooldown_duration:
                    cprint("stopping bot fully", "#AAE5A4")
                    if load_toml_as_dict("cfg/general_config.toml").get("alarm_enabled", True):
                        play_alarm()
                    self.stop_gracefully()
                    break

                if abs(s_time - t_now) > 1:
                    elapsed = t_now - s_time
                    if elapsed > 0:
                        ips = c / elapsed
                        bd = self.Stage_manager.brawlers_pick_data[0] if self.Stage_manager.brawlers_pick_data else {}
                        bname = bd.get("brawler", "?")
                        tro = self.Stage_manager.Trophy_observer.current_trophies if hasattr(self.Stage_manager, "Trophy_observer") else bd.get("trophies", "?")
                        st = self.get_latest_state() or "?"
                        w_streak = self.Stage_manager.Trophy_observer.win_streak if hasattr(self.Stage_manager, "Trophy_observer") else None
                        wins = self.Stage_manager.Trophy_observer.current_wins if hasattr(self.Stage_manager, "Trophy_observer") else None
                        self.telemetry.update_run(
                            bot_status="Running",
                            emulator_status="Connected",
                            current_state=format_state_label(st),
                            brawler=bname,
                            trophies=tro,
                            win_streak=w_streak or 0,
                            playstyle=self.current_playstyle_name,
                            ips=round(ips, 1),
                        )
                        render_terminal_dashboard(
                            self.telemetry.snapshot(),
                            version=IRIS_VERSION,
                            runtime_dir=str(get_runtime_dir()),
                            debug=DEBUG_MODE,
                        )
                    s_time = t_now
                    c = 0

                self.check_and_handle_brawl_stars_crash()

                frame, last_ft = self.window_controller.get_latest_frame()
                if frame is None:
                    frame = self.window_controller.screenshot()
                else:
                    frame_age = t_now - last_ft
                    if frame_age > self.window_controller.FRAME_STALE_TIMEOUT:
                        self.Play.window_controller.release_movement()
                        if frame_age > 30:
                            print(f"Scrcpy feed stale for {frame_age:.0f}s -- attempting reconnect")
                            if not self.window_controller.reconnect_scrcpy():
                                print("Reconnect failed -- restarting Brawl Stars")
                                self.restart_brawl_stars()
                        else:
                            print("Stale frame detected -- pausing actions until feed resumes")
                            if self.sleep_interruptible(1) == "stop":
                                self.stop_gracefully()
                                break
                        continue

                recovery_state = self.get_latest_state()
                recovery_messages = {
                    "idle_disconnect": "Idle disconnect detected. Restarting Brawl Stars.",
                    "app_not_responding": "Brawl Stars stopped responding. Restarting the app.",
                    "cannot_rejoin_battle": "Battle reconnect failed. Pressing Reload.",
                }
                if recovery_state in recovery_messages:
                    self.telemetry.emit("warning", recovery_messages[recovery_state])
                    self.handle_detected_state(recovery_state)
                    continue

                self.manage_time_tasks(frame)
                if self.should_stop():
                    self.stop_gracefully()
                    break

                brawler = self.Stage_manager.brawlers_pick_data[0]['brawler']
                self.Play.current_brawler = brawler
                self.Play.main(frame, brawler, self, last_ft)
                c += 1

                if self.max_ips:
                    target_period = 1 / self.max_ips
                    work_time = time.perf_counter() - iter_start
                    if work_time < target_period:
                        time.sleep(target_period - work_time)

                fps_counter += 1
                elapsed_fps = time.perf_counter() - fps_timer
                if elapsed_fps >= 5.0:
                    actual_fps = fps_counter / elapsed_fps
                    if actual_fps < 15:
                        print(f"WARNING: Low iteration rate ({actual_fps:.1f} IPS) — reducing load may help")
                    fps_timer = time.perf_counter()
                    fps_counter = 0

    runtime_path("debug_frames", create_parent=False).mkdir(parents=True, exist_ok=True)
    main = Main()
    main.main()


all_brawlers = get_brawler_list()
if api_base_url != "localhost":
    update_missing_brawlers_info(all_brawlers)
    check_version()
    update_wall_model_classes()
    if not current_wall_model_is_latest():
        print("New Wall detection model found, downloading... (this might take a few minutes depending on your internet)")
        get_latest_wall_model_file()


def find_open_port(start_port=5185, host="127.0.0.1"):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError("Could not find an open localhost port for the Flask UI.")


def open_browser_later(local_url):
    def _open():
        time.sleep(1.5)
        webbrowser.open(local_url)

    threading.Thread(target=_open, daemon=True, name="iris-browser-launcher").start()


def cli_entry_point():
    """CLI entry point for 'iris' command."""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        from install import main as install_main
        install_main()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "self-update":
        import subprocess
        print("Checking for updates...")
        try:
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
            result = subprocess.run(["git", "rev-list", "--count", "HEAD..origin/main"],
                                   check=True, capture_output=True, text=True)
            commits_behind = int(result.stdout.strip())
            if commits_behind > 0:
                print(f"Found {commits_behind} new commit(s). Updating...")
                subprocess.run(["git", "pull"], check=True)
                subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
                print("Update complete. Restart the bot.")
            else:
                print("Already up to date.")
        except subprocess.CalledProcessError as e:
            print(f"Update failed: {e}")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "update-models":
        from install import download_models
        download_models()
        return

    main()


def main():
    if sys.platform != "darwin":
        raise RuntimeError("IrisAI supports macOS only.")
    session_capture = setup_session_logging(enabled=LOG_MODE, debug=DEBUG_MODE, version=IRIS_VERSION)
    telemetry = get_runtime_telemetry()
    telemetry.configure_logging(
        enabled=LOG_MODE,
        path=str(session_capture.path) if session_capture.path else None,
    )
    if session_capture.path:
        telemetry.emit("system", f"Session logging enabled: {session_capture.path}")

    shutdown_signal = None
    previous_signal_handlers = {}

    def request_graceful_shutdown(signum, _frame):
        nonlocal shutdown_signal
        shutdown_signal = signal.Signals(signum).name.lower()
        raise KeyboardInterrupt

    graceful_signals = [signal.SIGTERM]
    if hasattr(signal, "SIGHUP"):
        graceful_signals.append(signal.SIGHUP)
    for graceful_signal in graceful_signals:
        previous_signal_handlers[graceful_signal] = signal.getsignal(graceful_signal)
        signal.signal(graceful_signal, request_graceful_shutdown)

    sys.excepthook = _global_exception_handler
    exit_reason = "stopped"
    app = None
    try:
        port = find_open_port()
        app = create_app(iris_main, start_discord_bot=True)
        local_url = f"http://127.0.0.1:{port}"
        telemetry.emit("system", f"Web UI ready at {local_url}.")
        render_terminal_dashboard(
            telemetry.snapshot(),
            version=IRIS_VERSION,
            runtime_dir=str(get_runtime_dir()),
            debug=DEBUG_MODE,
        )

        logging.getLogger('werkzeug').setLevel(logging.DEBUG if DEBUG_MODE else logging.ERROR)
        open_browser_later(local_url)
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        exit_reason = shutdown_signal or "ctrl_c"
        stop_method = shutdown_signal.upper() if shutdown_signal else "Ctrl+C"
        telemetry.emit("system", f"Application stopped with {stop_method}.")
    except Exception as exc:
        exit_reason = "crashed"
        telemetry.update_run(bot_status="Error")
        telemetry.emit("error", "IrisAI stopped unexpectedly.", details=traceback.format_exc())
        raise
    finally:
        runtime_manager = getattr(app, "config", {}).get("runtime_manager") if app is not None else None
        if runtime_manager is not None:
            runtime_manager.shutdown(timeout=10.0)
        for graceful_signal, previous_handler in previous_signal_handlers.items():
            signal.signal(graceful_signal, previous_handler)
        if exit_reason == "stopped":
            telemetry.emit("system", "Application stopped.")
        if session_capture.path:
            telemetry.configure_logging(enabled=True, path=str(session_capture.path), status="saved")
        session_capture.close(snapshot=telemetry.snapshot(), reason=exit_reason)


def _global_exception_handler(exctype, value, tb):
    if issubclass(exctype, KeyboardInterrupt):
        sys.__excepthook__(exctype, value, tb)
        return
    get_runtime_telemetry().update_run(bot_status="Error")
    get_runtime_telemetry().emit("error", "IrisAI stopped unexpectedly.", details=str(value))
    print_crash_banner()
    capture = getattr(sys.stderr, "capture", None)
    if capture is not None and not capture.enabled:
        traceback.print_exception(exctype, value, tb, file=sys.__stderr__)
    else:
        sys.__excepthook__(exctype, value, tb)


if __name__ == "__main__":
    main()

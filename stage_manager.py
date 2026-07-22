import time
import cv2

from state_finder import get_state
from trophy_observer import TrophyObserver, MatchResult
from config_loader import get_config
from utils import find_template_center, load_toml_as_dict, notify_user, save_brawler_data

try:
    from early_access.early_access import get_brawler_stats, get_player_info

    early_access = True
except (ImportError, ModuleNotFoundError):
    early_access = False


    def get_brawler_stats(_player_info, _brawler_name, _power_level=False):
        return None, None


    def get_player_info(_tag):
        return None


def load_image(image_path, scale_factor):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    orig_height, orig_width = image.shape[:2]

    new_width = int(orig_width * scale_factor)
    new_height = int(orig_height * scale_factor)

    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image


class StageManager:
    MATCH_STARTING_STATES = {
        "match_making",
        "loading",
        "match_intro",
        "brawler_selection",
    }

    def __init__(self, brawlers_data, lobby_automator, window_controller, playstyle_info, state_getting, runtime_control=None):
        self.Lobby_automation = lobby_automator
        self.lobby_config = load_toml_as_dict("./cfg/lobby_config.toml")
        self.close_popup_icon = None
        self.brawlers_pick_data = brawlers_data
        self.Trophy_observer = TrophyObserver()
        self.time_since_last_stat_change = time.time()
        self.play_again_on_win = get_config("cfg/bot_config.toml", "play_again_on_win", True)
        self.window_controller = window_controller
        self.states = {
            'shop': self.quit_shop,
            'brawler_selection': lambda: 0,
            'popup': self.close_pop_up,
            'match': lambda: 0,
            'loading': lambda: 0,
            'match_intro': lambda: 0,
            'spectating': lambda: 0,
            'match_making': lambda: 0,
            'lobby': self.start_game,
            'star_drop_regular': lambda: self.click_star_drop("regular"),
            'star_drop_angelic': lambda: self.click_star_drop("angelic"),
            'star_drop_demonic': lambda: self.click_star_drop("demonic"),
            'star_drop_starr_nova': lambda: self.click_star_drop("starr_nova"),
            'trophy_reward': lambda: self.window_controller.press("proceed"),
            'prestige_milestone': lambda: self.window_controller.press("continue_or_equip"),
            'end_draw': self.end_game,
            'end_victory': self.end_game,
            'end_defeat': self.end_game,
            'end_trio_showdown_0': self.end_game,
            'end_trio_showdown_1': self.end_game,
            'end_trio_showdown_2': self.end_game,
            'end_trio_showdown_3': self.end_game,
            'nano_noodles': self.click_nano_noodles,
            'idle_disconnect': self.handle_idle_disconnect,
            'app_not_responding': self.handle_app_not_responding,
            'cannot_rejoin_battle': self.handle_cannot_rejoin_battle,
        }
        self.matches_since_last_webhook_ping = 0
        self.ping_every_x_match = get_config("cfg/webhook_config.toml", "ping_every_x_match", 0)
        self.runtime_control = runtime_control
        if early_access:
            self.player_tag = get_config("cfg/general_config.toml", "player_tag", "")
        self.ping_when_stuck = get_config("cfg/webhook_config.toml", "ping_when_stuck", True)
        self.playstyle_info = playstyle_info
        self.get_latest_state = state_getting
        bot_config = load_toml_as_dict("./cfg/bot_config.toml")
        self.max_losses = int(bot_config.get("max_losses", 0))
        self.max_consecutive_losses = int(bot_config.get("max_consecutive_losses", 0))
        self._pending_brawler_switch = False

    def _should_stop(self):
        return bool(self.runtime_control and self.runtime_control.should_stop())

    def _should_pause(self):
        return bool(self.runtime_control and self.runtime_control.should_pause())

    def _sleep_interruptible(self, duration, allow_pause=True, poll_interval=0.1):
        end_time = time.time() + duration
        while time.time() < end_time:
            if self._should_stop():
                return True
            if allow_pause and self._should_pause():
                return True
            time.sleep(min(poll_interval, max(end_time - time.time(), 0)))
        return False

    @staticmethod
    def validate_trophies(trophies_string):
        trophies_string = trophies_string.lower()
        while "s" in trophies_string:
            trophies_string = trophies_string.replace("s", "5")
        numbers = ''.join(filter(str.isdigit, trophies_string))

        if not numbers:
            return False

        trophy_value = int(numbers)
        return trophy_value

    def start_game(self):
        if not self.brawlers_pick_data:
            return
        if self._should_stop() or self._should_pause():
            return

        if early_access and self.player_tag:
            print("Waiting 3 seconds for API to update with latest data...")
            time.sleep(3)
            player_info = get_player_info(self.player_tag)
            if not player_info:
                print("Player tag is incorrect. Use your Brawl Stars player tag, not your Supercell ID. Skipping API stat refresh.")
            else:
                current_brawler = self.brawlers_pick_data[0]['brawler']
                trophies, win_streak = get_brawler_stats(player_info, current_brawler)
                if trophies is not None and win_streak is not None:
                    if trophies != self.Trophy_observer.current_trophies or win_streak != self.Trophy_observer.win_streak:
                        print(f"Warning: Trophies or win streak from API do not match current values. This may indicate a desync. API values: trophies={trophies}, win_streak={win_streak}. Current values: trophies={self.Trophy_observer.current_trophies}, win_streak={self.Trophy_observer.win_streak}")
                    self.Trophy_observer.current_trophies = trophies
                    self.Trophy_observer.win_streak = win_streak
        print("state is lobby, starting game")

        if self._pending_brawler_switch:
            self._pending_brawler_switch = False
            brawler_name = self.brawlers_pick_data[0]['brawler']
            print(f"Pending brawler switch detected — auto-picking {brawler_name}")
            if self.brawlers_pick_data[0]["automatically_pick"]:
                result = self.Lobby_automation.select_brawler(brawler_name, self.get_latest_state, runtime_control=self.runtime_control)
                if result in ("aborted", "stuck"):
                    print(f"Brawler selection returned {result} — skipping match start")
                    return
                attempts = 0
                while result in ["failed", "error"] and attempts < len(self.brawlers_pick_data):
                    attempts += 1
                    if self.ping_when_stuck:
                        screenshot = self.window_controller.screenshot()
                        notify_user("bot_failed_brawler_selection", screenshot, self)
                    failed = self.brawlers_pick_data.pop(0)
                    self.brawlers_pick_data.append(failed)
                    brawler_name = self.brawlers_pick_data[0]['brawler']
                    self.quit_shop()
                    result = self.Lobby_automation.select_brawler(brawler_name, self.get_latest_state, runtime_control=self.runtime_control)
                if result == "success":
                    self.Trophy_observer.change_trophies(self.brawlers_pick_data[0]['trophies'])
                    self.Trophy_observer.current_wins = self.brawlers_pick_data[0]['wins'] if self.brawlers_pick_data[0]['wins'] != "" else 0
                    self.Trophy_observer.win_streak = self.brawlers_pick_data[0]['win_streak']
                    save_brawler_data(self.brawlers_pick_data)
                if result != "success":
                    print(f"Brawler switch returned {result} — skipping match start")
                    return
                print(f"Brawler switch result: success")

        values = {
            "trophies": self.Trophy_observer.current_trophies,
            "wins": self.Trophy_observer.current_wins
        }

        type_of_push = self.brawlers_pick_data[0]['type']
        value = values.get(type_of_push, 0)
        push_current_brawler_till = self.brawlers_pick_data[0]['push_until']

        if value >= push_current_brawler_till:
            if len(self.brawlers_pick_data) <= 1:
                print("Brawler reached required trophies/wins. No more brawlers selected for pushing in the menu. "
                      "Bot will now pause itself until closed.", value, push_current_brawler_till)
                screenshot = self.window_controller.screenshot()
                notify_user("completed", screenshot, self)
                print("Bot stopping: all targets completed with no more brawlers.")
                self.window_controller.release_movement()
                self.window_controller.close()
                if self.runtime_control:
                    self.runtime_control.request_stop()
                    self.runtime_control.mark_completed("All targets reached")
                return
            ping_when_target_is_reached = load_toml_as_dict("cfg/webhook_config.toml").get("ping_when_target_is_reached", False)
            if ping_when_target_is_reached:
                screenshot = self.window_controller.screenshot()
                notify_user("brawler_goal", screenshot, self)
            print(f'Bot has reached the target trophies/wins for {self.brawlers_pick_data[0]["brawler"]}, moving on to the next one in the list.', value, push_current_brawler_till)
            self.brawlers_pick_data.pop(0)
            next_brawler_name = self.brawlers_pick_data[0]['brawler']
            if self.brawlers_pick_data[0]["automatically_pick"]:
                select_brawler = self.Lobby_automation.select_brawler(next_brawler_name, self.get_latest_state, runtime_control=self.runtime_control)
                while select_brawler in ["failed", "error"]:
                    if self.ping_when_stuck:
                        screenshot = self.window_controller.screenshot()
                        notify_user("bot_failed_brawler_selection", screenshot, self)
                        print(f"Skipping {select_brawler}")
                    if self._should_stop() or self._should_pause():
                        return
                    current_brawler = self.brawlers_pick_data.pop(0)
                    self.brawlers_pick_data.append(current_brawler)
                    next_brawler_name = self.brawlers_pick_data[0]['brawler']
                    self.quit_shop()
                    select_brawler = self.Lobby_automation.select_brawler(next_brawler_name, self.get_latest_state, runtime_control=self.runtime_control)
                if select_brawler == "aborted" or select_brawler == "stuck":
                    return
                if select_brawler == "success":
                    self.Trophy_observer.change_trophies(self.brawlers_pick_data[0]['trophies'])
                    self.Trophy_observer.current_wins = self.brawlers_pick_data[0]['wins'] if self.brawlers_pick_data[0]['wins'] != "" else 0
                    self.Trophy_observer.win_streak = self.brawlers_pick_data[0]['win_streak']
            else:
                self.Trophy_observer.change_trophies(self.brawlers_pick_data[0]['trophies'])
                self.Trophy_observer.current_wins = self.brawlers_pick_data[0]['wins'] if self.brawlers_pick_data[0]['wins'] != "" else 0
                self.Trophy_observer.win_streak = self.brawlers_pick_data[0]['win_streak']
                print("Next brawler is in manual mode, waiting 10 seconds to let user switch.")
                if self._sleep_interruptible(10):
                    return
        save_brawler_data(self.brawlers_pick_data)
        self.matches_since_last_webhook_ping += 1
        if self.ping_every_x_match and self.matches_since_last_webhook_ping >= self.ping_every_x_match:
            screenshot = self.window_controller.screenshot()
            notify_user("regular_matches_ping", screenshot, self)
            self.matches_since_last_webhook_ping = 0

        if self._should_stop() or self._should_pause():
            return
        self.window_controller.release_movement()
        self.window_controller.press("proceed")
        print("Pressed to start a match")
        time.sleep(2)

    def click_star_drop(self, drop_type="regular"):
        if hasattr(self, '_star_drop_thread') and self._star_drop_thread.is_alive():
            return

        def _handle_drop():
            if drop_type in ["angelic", "demonic", "starr_nova"]:
                self.window_controller.press("proceed", 8)
            else:
                for _ in range(8):
                    self.window_controller.press("proceed", 0.05)
                    time.sleep(0.1)

        import threading
        self._star_drop_thread = threading.Thread(target=_handle_drop, daemon=True)
        self._star_drop_thread.start()

    def click_nano_noodles(self):
        noodle_x, noodle_y = 960, 740
        offset_x = 330
        self.window_controller.click(
            noodle_x,
            noodle_y,
            already_include_ratio=False
        )
        time.sleep(0.1)
        self.window_controller.click(
            noodle_x + offset_x,
            noodle_y,
            already_include_ratio=False
        )
        time.sleep(0.1)
        self.window_controller.click(
            noodle_x - offset_x,
            noodle_y,
            already_include_ratio=False
        )

    def _rotate_to_lowest_trophy_brawler(self):
        if len(self.brawlers_pick_data) <= 1:
            return False
        current_brawler = self.brawlers_pick_data[0]['brawler']
        candidates = [(i, entry) for i, entry in enumerate(self.brawlers_pick_data)
                      if entry['brawler'] != current_brawler]
        if not candidates:
            return False
        candidates.sort(key=lambda x: int(x[1].get('trophies', 0) or 0))
        lowest_idx, lowest_entry = candidates[0]
        self.brawlers_pick_data.pop(lowest_idx)
        self.brawlers_pick_data.insert(0, lowest_entry)
        self.brawlers_pick_data[0]['automatically_pick'] = True
        self._pending_brawler_switch = True
        print(f"Loss threshold reached. Switching to lowest-trophy brawler: {self.brawlers_pick_data[0]['brawler']}")
        self.Trophy_observer.reset_losses()
        save_brawler_data(self.brawlers_pick_data)
        return True

    def end_game(self):
        if not self.brawlers_pick_data:
            return
        screenshot = self.window_controller.screenshot()

        current_state = get_state(screenshot)
        button_pressed = False
        end_screen_time = time.time()
        parsed_result = None
        while current_state and current_state.startswith("end") and time.time() - end_screen_time < 35:

            if time.time() - self.time_since_last_stat_change > 25 and parsed_result is None :
                raw_found_result = '_'.join(current_state.split("_")[1:])
                parsed_result = self.Trophy_observer.parse_game_result(raw_found_result)

                current_brawler = self.brawlers_pick_data[0]['brawler']
                power_level = None
                if early_access:
                    player_info = get_player_info(self.player_tag)
                    if player_info is not None:
                        power_level = get_brawler_stats(player_info, current_brawler, power_level=True)[2]
                self.Trophy_observer.add_trophies(parsed_result, current_brawler, self.playstyle_info, power_level)
                self.Trophy_observer.add_win(parsed_result)
                self.time_since_last_stat_change = time.time()
                values = {
                    "trophies": self.Trophy_observer.current_trophies,
                    "wins": self.Trophy_observer.current_wins
                }
                type_to_push = self.brawlers_pick_data[0]['type']
                value = values[type_to_push]
                self.brawlers_pick_data[0][type_to_push] = value
                self.brawlers_pick_data[0]['win_streak'] = self.Trophy_observer.win_streak
                save_brawler_data(self.brawlers_pick_data)

                if parsed_result and parsed_result.result == MatchResult.DEFEAT:
                    max_loss_ok = self.max_losses > 0 and self.Trophy_observer.total_losses >= self.max_losses
                    max_streak_ok = self.max_consecutive_losses > 0 and self.Trophy_observer.lose_streak >= self.max_consecutive_losses
                    if max_loss_ok or max_streak_ok:
                        trigger = "max_losses" if max_loss_ok else "max_consecutive_losses"
                        print(f"{trigger}={self.Trophy_observer.total_losses if max_loss_ok else self.Trophy_observer.lose_streak} reached — switching brawler")
                        self._rotate_to_lowest_trophy_brawler()

            if not button_pressed and self.play_again_on_win and parsed_result and parsed_result.result == MatchResult.VICTORY and not self._should_pause() and not self._should_stop():
                self.window_controller.press("play_again")
                button_pressed = True
            else:
                print("Game has ended, proceeding")
                self.window_controller.press("proceed")

            time.sleep(3)
            screenshot = self.window_controller.screenshot()
            current_state = get_state(screenshot)

        if self.play_again_on_win and parsed_result and parsed_result.result == MatchResult.VICTORY and not self._should_pause():
            self.wait_for_next_match()
        elif time.time() - end_screen_time > 35:
            print("End screen timeout reached, restarting the game.")
            self.window_controller.restart_brawl_stars()
        print("Game has ended", current_state)

    def wait_for_next_match(self, timeout=25):
        print("Waiting for matchmaking...")
        start_wait_time = time.time()
        while time.time() - start_wait_time < timeout:
            if self._should_stop() or self._should_pause():
                return False

            screenshot = self.window_controller.screenshot()
            current_state = get_state(screenshot)
            if current_state == "match":
                print("Match started successfully!")
                return True
            if current_state in self.MATCH_STARTING_STATES:
                readable_state = "Matchmaking" if current_state == "match_making" else current_state.replace("_", " ").title()
                print(f"Entered {readable_state}; waiting in the normal state loop.")
                return True
            if current_state == "lobby":
                print("Returned to the lobby; the normal state loop will queue again.")
                return True
            if self._sleep_interruptible(0.5):
                return False

        print(f"No matchmaking progress within {timeout}s, restarting the game.")
        self.window_controller.restart_brawl_stars()
        time.sleep(2)
        return False

    def handle_idle_disconnect(self):
        print("Idle disconnect detected — restarting Brawl Stars")
        self.window_controller.release_movement()
        self.window_controller.restart_brawl_stars()
        self.Trophy_observer.reset_losses()

    def handle_app_not_responding(self):
        print("Android reports that Brawl Stars is not responding — restarting the app")
        self.window_controller.release_movement()
        self.window_controller.restart_brawl_stars()

    def handle_cannot_rejoin_battle(self):
        print("Cannot rejoin battle detected — pressing Reload")
        self.window_controller.release_movement()
        self.window_controller.press("idle_reconnect")
        time.sleep(2)

    def quit_shop(self):
        self.window_controller.click(100 * self.window_controller.width_ratio, 60 * self.window_controller.height_ratio)
        time.sleep(1)

    def close_pop_up(self):
        screenshot = self.window_controller.screenshot()
        if self.close_popup_icon is None:
            self.close_popup_icon = load_image("images/states/close_popup.png", self.window_controller.scale_factor)
        popup_location = find_template_center(screenshot, self.close_popup_icon)
        if popup_location:
            self.window_controller.click(*popup_location)

    def do_state(self, state, data=None):
        if data is None:
            self.states[state]()
        else:
            self.states[state](data)

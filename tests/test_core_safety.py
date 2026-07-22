import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

import numpy as np


class QueueCleaningTests(unittest.TestCase):
    def test_clean_queue_skips_bad_items_and_fills_defaults(self):
        from utils import clean_queue

        result = clean_queue([
            "bad",
            {"type": "wins"},
            {"brawler": "Shelly", "type": "trophies", "trophies": "10", "push_until": "20"},
            {"brawler": "Colt", "type": "unknown", "push_until": "5"},
        ])

        self.assertEqual(
            result,
            [
                {
                    "brawler": "Shelly",
                    "type": "trophies",
                    "trophies": 10,
                    "wins": 0,
                    "push_until": 20,
                    "automatically_pick": True,
                    "win_streak": 0,
                },
                {
                    "brawler": "Colt",
                    "type": "trophies",
                    "trophies": 0,
                    "wins": 0,
                    "push_until": 5,
                    "automatically_pick": True,
                    "win_streak": 0,
                },
            ],
        )


class RuntimeCaptureRetentionTests(unittest.TestCase):
    def test_retention_keeps_newest_files_under_count_limit(self):
        from runtime_paths import prune_runtime_files

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            for index in range(5):
                path = directory / f"capture-{index}.png"
                path.write_bytes(bytes([index]) * 10)
                os.utime(path, (index + 1, index + 1))

            deleted_count, deleted_bytes = prune_runtime_files(
                directory,
                patterns=("*.png",),
                max_files=2,
                max_bytes=1000,
            )

            self.assertEqual(deleted_count, 3)
            self.assertEqual(deleted_bytes, 30)
            self.assertEqual(
                sorted(path.name for path in directory.glob("*.png")),
                ["capture-3.png", "capture-4.png"],
            )

    def test_retention_keeps_newest_files_under_size_limit(self):
        from runtime_paths import prune_runtime_files

        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            for index in range(3):
                path = directory / f"capture-{index}.png"
                path.write_bytes(bytes([index]) * 60)
                os.utime(path, (index + 1, index + 1))

            prune_runtime_files(
                directory,
                patterns=("*.png",),
                max_files=10,
                max_bytes=100,
            )

            self.assertEqual(
                [path.name for path in directory.glob("*.png")],
                ["capture-2.png"],
            )


class MacOnlyPlatformTests(unittest.TestCase):
    def test_installer_rejects_non_macos_platforms(self):
        import install

        with patch("install.platform.system", return_value="UnsupportedOS"):
            with self.assertRaisesRegex(RuntimeError, "macOS"):
                install.detect_platform()

    def test_onnx_provider_candidates_are_coreml_then_cpu_only(self):
        from detect import _macos_provider_candidates

        available = [
            "UnsupportedAcceleratorExecutionProvider",
            "CoreMLExecutionProvider",
            "CPUExecutionProvider",
        ]

        self.assertEqual(
            _macos_provider_candidates("auto", available),
            ["CoreMLExecutionProvider", "CPUExecutionProvider"],
        )
        self.assertEqual(
            _macos_provider_candidates("cpu", available),
            ["CPUExecutionProvider"],
        )

    def test_onnx_provider_candidates_reject_old_profiles(self):
        from detect import _macos_provider_candidates

        with self.assertRaisesRegex(ValueError, "auto.*coreml.*cpu"):
            _macos_provider_candidates("legacy-gpu", ["CPUExecutionProvider"])


class StateFinderTests(unittest.TestCase):
    def test_template_larger_than_region_returns_false(self):
        from state_finder import is_template_in_region

        image = np.zeros((10, 10, 3), dtype=np.uint8)
        result = is_template_in_region(
            image,
            "images/states/lobby_menu.png",
            [0, 0, 1, 1],
        )

        self.assertFalse(result)

    def test_empty_region_returns_false(self):
        from state_finder import is_template_in_region

        image = np.zeros((10, 10, 3), dtype=np.uint8)
        result = is_template_in_region(
            image,
            "images/states/lobby_menu.png",
            [50, 50, 1, 1],
        )

        self.assertFalse(result)

    def test_current_idle_disconnect_template_is_detectable(self):
        import cv2
        from state_finder import is_in_idle_disconnect

        template = cv2.imread("images/states/idle_disconnect.png")
        self.assertIsNotNone(template)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        height, width = template.shape[:2]
        image[420:420 + height, 480:480 + width] = template

        self.assertTrue(is_in_idle_disconnect(image))

    def test_recovery_alert_templates_are_detectable(self):
        import cv2
        from state_finder import is_app_not_responding, is_cannot_rejoin_battle

        cases = [
            ("images/states/app_not_responding.png", is_app_not_responding, 490, 440),
            ("images/states/cannot_rejoin_battle.png", is_cannot_rejoin_battle, 490, 415),
        ]
        for template_path, detector, x, y in cases:
            with self.subTest(template=template_path):
                template = cv2.imread(template_path)
                self.assertIsNotNone(template)
                template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
                image = np.zeros((1080, 1920, 3), dtype=np.uint8)
                height, width = template.shape[:2]
                image[y:y + height, x:x + width] = template
                self.assertTrue(detector(image))

    def test_loading_templates_are_detectable(self):
        import cv2
        from state_finder import is_app_loading

        cases = [
            ("images/states/brawl_loading_logo.png", 30, 25),
            ("images/states/app_launch_icon.png", 800, 380),
        ]
        for template_path, x, y in cases:
            with self.subTest(template=template_path):
                template = cv2.imread(template_path)
                self.assertIsNotNone(template)
                template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
                image = np.zeros((1080, 1920, 3), dtype=np.uint8)
                height, width = template.shape[:2]
                image[y:y + height, x:x + width] = template
                self.assertTrue(is_app_loading(image))

    def test_nano_noodles_uses_specific_daily_wins_signature(self):
        import cv2
        from state_finder import is_in_nano_noodles

        template = cv2.imread("images/states/nano_noodles_daily_wins.png")
        self.assertIsNotNone(template)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        height, width = template.shape[:2]
        image[0:height, 0:width] = template

        self.assertTrue(is_in_nano_noodles(image))

    def test_match_intro_and_spectator_templates_are_detectable(self):
        import cv2
        from state_finder import is_match_intro, is_spectating

        cases = [
            ("images/states/match_intro_vs.png", is_match_intro, 890, 475),
            ("images/states/spectating_following.png", is_spectating, 1520, 925),
        ]
        for template_path, detector, x, y in cases:
            with self.subTest(template=template_path):
                template = cv2.imread(template_path)
                self.assertIsNotNone(template)
                template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
                image = np.zeros((1080, 1920, 3), dtype=np.uint8)
                height, width = template.shape[:2]
                image[y:y + height, x:x + width] = template
                self.assertTrue(detector(image))


class MovementInputTests(unittest.TestCase):
    @staticmethod
    def make_controller():
        import threading
        from window_controller import WindowController

        controller = WindowController.__new__(WindowController)
        controller.joystick_x = 220
        controller.joystick_y = 870
        controller.PID_JOYSTICK = 1
        controller._move_lock = threading.RLock()
        controller.are_we_moving = False
        controller.last_joystick_pos = (None, None)
        controller.re_apply_movement = False
        controller._last_movement_log_time = 0.0
        controller.touch_down = Mock(return_value=True)
        controller.touch_move = Mock(return_value=True)
        controller.touch_up = Mock(return_value=True)
        return controller

    def test_successful_movement_is_marked_active(self):
        controller = self.make_controller()

        with patch("builtins.print"):
            self.assertTrue(controller.move(0, -75))

        self.assertTrue(controller.are_we_moving)
        self.assertEqual(controller.last_joystick_pos, (220, 795))

    def test_failed_movement_is_not_marked_active(self):
        controller = self.make_controller()
        controller.touch_move.return_value = False

        with patch("builtins.print"):
            self.assertFalse(controller.move(0, -75))

        self.assertFalse(controller.are_we_moving)
        controller.touch_up.assert_called_once()


class NanoNoodlesActionTests(unittest.TestCase):
    def test_nano_noodles_selects_three_center_options(self):
        from stage_manager import StageManager

        manager = StageManager.__new__(StageManager)
        manager.window_controller = Mock()

        with patch("stage_manager.time.sleep"):
            manager.click_nano_noodles()

        self.assertEqual(
            manager.window_controller.click.call_args_list,
            [
                call(960, 740, already_include_ratio=False),
                call(1290, 740, already_include_ratio=False),
                call(630, 740, already_include_ratio=False),
            ],
        )


class MatchmakingStateTests(unittest.TestCase):
    def test_matchmaking_uses_standard_dashboard_label(self):
        from main import format_state_label

        self.assertEqual(format_state_label("match_making"), "Matchmaking")

    def test_matchmaking_is_progress_and_does_not_restart_the_app(self):
        from stage_manager import StageManager

        manager = StageManager.__new__(StageManager)
        manager.window_controller = Mock()
        manager.runtime_control = None

        with (
            patch("stage_manager.get_state", return_value="match_making"),
            patch("stage_manager.time.sleep"),
            patch("builtins.print"),
        ):
            result = manager.wait_for_next_match()

        self.assertTrue(result)
        manager.window_controller.restart_brawl_stars.assert_not_called()

    def test_matchmaking_timeout_still_restarts_the_app(self):
        from stage_manager import StageManager

        manager = StageManager.__new__(StageManager)
        manager.window_controller = Mock()
        manager.runtime_control = None

        with (
            patch("stage_manager.get_state", return_value="end_victory"),
            patch("stage_manager.time.time", side_effect=[0, 0, 2]),
            patch("stage_manager.time.sleep"),
            patch.object(manager, "_sleep_interruptible", return_value=False),
            patch("builtins.print"),
        ):
            result = manager.wait_for_next_match(timeout=1)

        self.assertFalse(result)
        manager.window_controller.restart_brawl_stars.assert_called_once_with()


class MacOSVisionOCRTests(unittest.TestCase):
    def test_native_observations_use_easyocr_compatible_coordinates(self):
        from utils import MacOSVisionOCR

        results = MacOSVisionOCR._to_easyocr_results([
            {
                "text": "MORTIS",
                "confidence": 0.99,
                "box": [100.0, 200.0, 80.0, 40.0],
            }
        ])

        self.assertEqual(
            results,
            [
                (
                    [[100.0, 200.0], [180.0, 200.0], [180.0, 240.0], [100.0, 240.0]],
                    "MORTIS",
                    0.99,
                )
            ],
        )


class BrawlerSelectionTests(unittest.TestCase):
    def test_text_match_clicks_brawler_then_select(self):
        from lobby_automation import LobbyAutomation

        class FakeWindowController:
            width_ratio = 1.0
            height_ratio = 1.0

            def __init__(self):
                self.clicks = []

            def screenshot(self):
                return np.zeros((1080, 1920, 3), dtype=np.uint8)

            def click(self, x, y, **_kwargs):
                self.clicks.append((x, y))

            def swipe(self, *_args, **_kwargs):
                raise AssertionError("Selection should not scroll after finding Mortis")

        controller = FakeWindowController()
        automation = LobbyAutomation(controller)
        automation.ocr_scale_down_factor = 1.0
        automation.ocr_scale_up_factor = 1.0
        detected = {
            "mortis": {
                "center": (900.0, 450.0),
                "top_left": (850.0, 430.0),
                "top_right": (950.0, 430.0),
                "bottom_right": (950.0, 470.0),
                "bottom_left": (850.0, 470.0),
            }
        }

        with (
            patch("lobby_automation.extract_text_and_positions", return_value=detected),
            patch("lobby_automation.get_ocr_engine_name", return_value="macOS Vision"),
            patch("lobby_automation.is_in_brawler_selection", return_value=True),
            patch("lobby_automation.is_in_lobby", return_value=False),
            patch("lobby_automation.time.sleep"),
            patch.object(LobbyAutomation, "_sleep_interruptible", return_value=False),
        ):
            result = automation.select_brawler("mortis", lambda: "brawler_selection")

        self.assertEqual(result, "success")
        self.assertEqual(controller.clicks[0], (110, 490))
        self.assertEqual(controller.clicks[1], (900, 400))
        self.assertEqual(controller.clicks[2], (150, 950))


class TrophyObserverTests(unittest.TestCase):
    def test_save_history_appends_only_new_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            previous_runtime_dir = os.environ.get("IRIS_RUNTIME_DIR")
            os.environ["IRIS_RUNTIME_DIR"] = temp_dir
            try:
                import pandas as pd
                from trophy_observer import TrophyObserver

                history_path = Path(temp_dir) / "match_history.csv"
                history_path.write_text(
                    "date_time,brawler_name,result,current_trophies,trophy_delta,new_winstreak,playstyle_hash,playstyle_name,playstyle_gamemodes,playstyle_brawlers,iris_version,power_level\n"
                    "2026-07-21T00:00:00,Shelly,victory,10,10,1,abc,Test,all,Shelly,0.0.1,-1\n",
                    encoding="utf-8",
                )

                observer = TrophyObserver()
                observer.match_history.loc[len(observer.match_history)] = [
                    "2026-07-21T00:01:00",
                    "Colt",
                    "defeat",
                    20,
                    -1,
                    0,
                    "def",
                    "Test",
                    "all",
                    "Colt",
                    "0.0.1",
                    -1,
                ]
                observer.save_history()

                saved = pd.read_csv(history_path)
                self.assertEqual(len(saved), 2)
                self.assertEqual(saved.iloc[0]["brawler_name"], "Shelly")
                self.assertEqual(saved.iloc[1]["brawler_name"], "Colt")
            finally:
                if previous_runtime_dir is None:
                    os.environ.pop("IRIS_RUNTIME_DIR", None)
                else:
                    os.environ["IRIS_RUNTIME_DIR"] = previous_runtime_dir

    def test_first_runtime_save_preserves_legacy_history(self):
        import pandas as pd
        from trophy_observer import TrophyObserver

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "match_history.csv"
            observer = TrophyObserver.__new__(TrophyObserver)
            observer._history_write_file = runtime_path
            observer.match_history = pd.DataFrame([
                {"brawler_name": "Shelly", "result": "victory"},
                {"brawler_name": "Colt", "result": "defeat"},
            ])
            observer._last_saved_index = 1

            observer.save_history()

            saved = pd.read_csv(runtime_path)
            self.assertEqual(saved["brawler_name"].tolist(), ["Shelly", "Colt"])


class PlaystyleSmokeTests(unittest.TestCase):
    @staticmethod
    def _context(with_entities):
        import math
        import random

        player = [900, 500, 1020, 620]
        enemies = [[1100, 500, 1180, 580]] if with_entities else []
        teammates = [[700, 500, 780, 580]] if with_entities else []

        def entity_pos(box):
            return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

        def closest(boxes, player_pos):
            if not boxes:
                return None, None
            position = entity_pos(boxes[0])
            return position, math.dist(position, player_pos)

        return {
            "player_data": player,
            "enemy_data": enemies,
            "teammate_data": teammates,
            "teammates_data": teammates,
            "brawler": "shelly",
            "walls": [],
            "bushes": [],
            "brawlers_info": {"shelly": {"hold_attack": 0, "super_type": "normal"}},
            "must_brawler_hold_attack": lambda *_args: False,
            "is_gadget_ready": False,
            "is_hypercharge_ready": False,
            "is_super_ready": False,
            "get_entity_pos": entity_pos,
            "get_brawler_range": lambda _brawler: [300, 500, 500],
            "is_there_enemy": bool,
            "is_there_teammate": bool,
            "count_enemies_in_area": lambda data, *_args: len(data),
            "count_teammates_in_area": lambda data, *_args: len(data),
            "find_closest_enemy": lambda data, pos, *_args: closest(data, pos),
            "find_closest_teammate": lambda data, pos, *_args: closest(data, pos),
            "is_path_blocked": lambda *_args: False,
            "is_enemy_hittable": lambda *_args: True,
            "attack": lambda **_kwargs: None,
            "use_hypercharge": lambda: None,
            "use_super": lambda: None,
            "use_gadget": lambda: None,
            "get_random_movement": lambda: (0, 0),
            "current_brawler": "shelly",
            "last_movement": (0, 0),
            "last_movement_change_time": 0,
            "seconds_to_hold_attack_after_reaching_max": 0,
            "width": 1920,
            "height": 1080,
            "time": time,
            "random": random,
            "persistent_data": {"time_since_holding_attack": None},
            "debug": False,
            "JOYSTICK_RADIUS": 75,
            "center": (960, 540),
            "rotate_movement": lambda movement, _angle: movement,
        }

    def test_every_playstyle_returns_movement_with_and_without_entities(self):
        from utils import interpret_iris_code, load_iris_script

        for script_path in sorted(Path("playstyles").glob("*.iris")):
            _metadata, script = load_iris_script(script_path.name)
            for with_entities in (False, True):
                with self.subTest(playstyle=script_path.name, with_entities=with_entities):
                    movement, _context = interpret_iris_code(script, self._context(with_entities))
                    self.assertIsInstance(movement, tuple)
                    self.assertEqual(len(movement), 2)


class WebUIRegressionTests(unittest.TestCase):
    def test_empty_runtime_history_returns_an_empty_payload(self):
        from webui.app import create_app

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_runtime_dir = os.environ.get("IRIS_RUNTIME_DIR")
            os.environ["IRIS_RUNTIME_DIR"] = temp_dir
            try:
                app = create_app(lambda *_args, **_kwargs: None)
                app.testing = True
                response = app.test_client().get("/api/history")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json()["summary"]["total_matches"], 0)
                self.assertEqual(response.get_json()["recent_matches"], [])
            finally:
                if previous_runtime_dir is None:
                    os.environ.pop("IRIS_RUNTIME_DIR", None)
                else:
                    os.environ["IRIS_RUNTIME_DIR"] = previous_runtime_dir

    def test_webhook_autosave_does_not_replace_masked_secrets(self):
        from webui.services import WebDataService

        service = WebDataService.__new__(WebDataService)
        existing = {
            "discord_bot_token": "real-token",
            "webhook_url": "https://example.invalid/hook",
            "ping_when_stuck": True,
        }
        service._load_config = Mock(return_value=existing.copy())
        service._save_config = Mock()

        service.update_settings("webhook", {
            "discord_bot_token": "••••••••",
            "webhook_url": "••••••••",
            "ping_when_stuck": False,
        })

        saved = service._save_config.call_args.args[1]
        self.assertEqual(saved["discord_bot_token"], "real-token")
        self.assertEqual(saved["webhook_url"], "https://example.invalid/hook")
        self.assertFalse(saved["ping_when_stuck"])


class HealthTests(unittest.TestCase):
    def test_health_report_has_expected_shape(self):
        from health import get_health_report

        report = get_health_report(include_optional=False)

        self.assertIn(report["status"], {"ok", "warning", "error"})
        self.assertIn("checks", report)
        self.assertIsInstance(report["checks"], list)


class RuntimeTelemetryTests(unittest.TestCase):
    def test_runtime_telemetry_keeps_session_summary_and_recent_match(self):
        from runtime_events import RuntimeTelemetry

        telemetry = RuntimeTelemetry()
        telemetry.start_session()
        telemetry.update_run(brawler="Shelly", trophies=500, playstyle="Survival")
        telemetry.record_match(
            brawler="Shelly",
            result="victory",
            trophy_delta=8,
            trophies=508,
            win_streak=2,
            playstyle="Survival",
            mode="classic",
        )

        snapshot = telemetry.snapshot()
        self.assertEqual(snapshot["session"]["matches"], 1)
        self.assertEqual(snapshot["session"]["wins"], 1)
        self.assertEqual(snapshot["session"]["trophy_delta"], 8)
        self.assertEqual(snapshot["current_run"]["last_result"], "victory")
        self.assertEqual(snapshot["recent_matches"][0]["brawler"], "Shelly")
        self.assertEqual(snapshot["recent_events"][0]["label"], "Match")

    def test_runtime_telemetry_exposes_session_logging_location(self):
        from runtime_events import RuntimeTelemetry

        telemetry = RuntimeTelemetry()
        telemetry.configure_logging(enabled=True, path="/tmp/iris-session.log")

        self.assertEqual(
            telemetry.snapshot()["logging"],
            {
                "enabled": True,
                "path": "/tmp/iris-session.log",
                "status": "recording",
            },
        )


class SessionLogCaptureTests(unittest.TestCase):
    def test_session_log_contains_output_exit_reason_and_summary(self):
        from terminal_ui import setup_session_logging

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_runtime_dir = os.environ.get("IRIS_RUNTIME_DIR")
            os.environ["IRIS_RUNTIME_DIR"] = temp_dir
            capture = None
            try:
                capture = setup_session_logging(enabled=True, version="test")
                print("diagnostic marker")
                capture.stdout_proxy.write(b"byte marker\n")
                capture.close(
                    snapshot={"session": {"matches": 2}, "recent_events": []},
                    reason="ctrl_c",
                    announce=False,
                )

                contents = capture.path.read_text(encoding="utf-8")
                self.assertIn("diagnostic marker", contents)
                self.assertIn("byte marker", contents)
                self.assertIn("exit_reason: ctrl_c", contents)
                self.assertIn('"matches": 2', contents)
                self.assertIn("=== End of IrisAI diagnostic session ===", contents)
            finally:
                if capture is not None:
                    capture.close(announce=False)
                if previous_runtime_dir is None:
                    os.environ.pop("IRIS_RUNTIME_DIR", None)
                else:
                    os.environ["IRIS_RUNTIME_DIR"] = previous_runtime_dir

    def test_uncaptured_crash_traceback_reaches_terminal(self):
        import io
        import main
        from terminal_ui import setup_session_logging

        capture = setup_session_logging(enabled=False, version="test")
        terminal = io.StringIO()
        try:
            try:
                raise RuntimeError("visible crash marker")
            except RuntimeError as error:
                with (
                    patch.object(main.sys, "__stderr__", terminal),
                    patch.object(main, "print_crash_banner"),
                ):
                    main._global_exception_handler(type(error), error, error.__traceback__)
        finally:
            capture.close(announce=False)

        self.assertIn("RuntimeError: visible crash marker", terminal.getvalue())


class RuntimeShutdownTests(unittest.TestCase):
    def test_shutdown_waits_for_runtime_worker(self):
        from webui.runtime import RuntimeManager

        def run_until_stopped(_discord_bot, _queue_data, runtime_control=None):
            while runtime_control and not runtime_control.should_stop():
                time.sleep(0.01)

        manager = RuntimeManager(run_until_stopped)
        manager.start([{"brawler": "Mortis"}], None)

        self.assertTrue(manager.shutdown(timeout=1.0))
        self.assertFalse(manager.get_status()["is_running"])


if __name__ == "__main__":
    unittest.main()

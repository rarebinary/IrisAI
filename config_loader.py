"""
config_loader.py — Safe configuration loading with defaults and type validation.
All config access goes through get_config() to prevent KeyError crashes.
"""
import os
import logging
from pathlib import Path
from typing import Any, Optional
from utils import load_toml_as_dict

logger = logging.getLogger(__name__)

# Mapping: (toml_path, toml_key) -> env_var_name
ENV_MAPPING = {
    ("cfg/webhook_config.toml", "discord_bot_token"): "IRIS_DISCORD_BOT_TOKEN",
    ("cfg/webhook_config.toml", "discord_id"): "IRIS_DISCORD_USER_ID",
    ("cfg/webhook_config.toml", "discord_guild_id"): "IRIS_DISCORD_GUILD_ID",
    ("cfg/webhook_config.toml", "webhook_url"): "IRIS_DISCORD_WEBHOOK_URL",
    ("cfg/webhook_config.toml", "telegram_token"): "IRIS_TELEGRAM_BOT_TOKEN",
    ("cfg/webhook_config.toml", "telegram_chat_id"): "IRIS_TELEGRAM_CHAT_ID",
    ("cfg/login.toml", "key"): "IRIS_API_KEY",
    ("cfg/general_config.toml", "api_base_url"): "IRIS_API_BASE_URL",
}

_env_loaded = False


def load_env_file() -> None:
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and value:
            os.environ.setdefault(key, value)


def get_env_override(path: str, key: str) -> str | None:
    env_var = ENV_MAPPING.get((path, key))
    if env_var:
        return os.environ.get(env_var)
    return None

CONFIG_DEFAULTS = {
    # general_config.toml
    ("cfg/general_config.toml", "max_ips"): "auto",
    ("cfg/general_config.toml", "run_for_minutes"): 60,
    ("cfg/general_config.toml", "trophies_multiplier"): 1.0,
    ("cfg/general_config.toml", "emulator_port"): 5555,
    ("cfg/general_config.toml", "api_base_url"): "localhost",
    ("cfg/general_config.toml", "brawl_stars_package"): "com.supercell.brawlstars",
    ("cfg/general_config.toml", "bs_package_name"): "com.supercell.brawlstars",
    ("cfg/general_config.toml", "ocr_scale_down_factor"): 0.75,
    ("cfg/general_config.toml", "process_every_n_frames"): 2,
    ("cfg/general_config.toml", "used_threads"): "auto",
    ("cfg/general_config.toml", "player_tag"): "",
    ("cfg/general_config.toml", "play_order"): "in_order",
    ("cfg/general_config.toml", "alarm_enabled"): True,
    ("cfg/general_config.toml", "default_trophy_target"): 750,
    ("cfg/general_config.toml", "auto_load_queue_on_startup"): False,
    ("cfg/general_config.toml", "cpu_or_gpu"): "auto",

    # bot_config.toml
    ("cfg/bot_config.toml", "play_again_on_win"): True,
    ("cfg/bot_config.toml", "minimum_movement_delay"): 0.05,
    ("cfg/bot_config.toml", "unstuck_movement_delay"): 20,
    ("cfg/bot_config.toml", "unstuck_movement_hold_time"): 3,
    ("cfg/bot_config.toml", "perceived_tile_size"): 80,
    ("cfg/bot_config.toml", "centered_wall_detection"): False,
    ("cfg/bot_config.toml", "entity_detection_confidence"): 0.5,
    ("cfg/bot_config.toml", "wall_detection_confidence"): 0.7,
    ("cfg/bot_config.toml", "re_apply_movement"): False,
    ("cfg/bot_config.toml", "current_playstyle"): "team_follow.iris",
    ("cfg/bot_config.toml", "max_losses"): 5,
    ("cfg/bot_config.toml", "max_consecutive_losses"): 3,
    ("cfg/bot_config.toml", "seconds_to_hold_attack_after_reaching_max"): 0.3,
    ("cfg/bot_config.toml", "super_pixels_minimum"): 1800,
    ("cfg/bot_config.toml", "gadget_pixels_minimum"): 1300,
    ("cfg/bot_config.toml", "hypercharge_pixels_minimum"): 1800,
    ("cfg/bot_config.toml", "idle_pixels_minimum"): 75000,
    ("cfg/bot_config.toml", "wall_model_classes"): ["wall", "bush", "close_bush"],

    # webhook_config.toml
    ("cfg/webhook_config.toml", "webhook_url"): "",
    ("cfg/webhook_config.toml", "discord_id"): "",
    ("cfg/webhook_config.toml", "discord_bot_token"): "",
    ("cfg/webhook_config.toml", "discord_guild_id"): "",
    ("cfg/webhook_config.toml", "telegram_token"): "",
    ("cfg/webhook_config.toml", "telegram_chat_id"): "",
    ("cfg/webhook_config.toml", "ping_when_stuck"): True,
    ("cfg/webhook_config.toml", "ping_when_target_is_reached"): True,
    ("cfg/webhook_config.toml", "ping_every_x_match"): 0,
    ("cfg/webhook_config.toml", "ping_every_x_minutes"): 0,

    # debug_settings.toml
    ("cfg/debug_settings.toml", "verbose_debug"): False,
    ("cfg/debug_settings.toml", "state_finder_debug"): False,
    ("cfg/debug_settings.toml", "re_apply_movement"): False,
    ("cfg/debug_settings.toml", "debug_view"): False,
    ("cfg/debug_settings.toml", "advanced_debug_visuals"): False,
    ("cfg/debug_settings.toml", "record_debug_preview_clips"): False,

    # time_tresholds.toml
    ("cfg/time_tresholds.toml", "state_check"): 3.0,
    ("cfg/time_tresholds.toml", "no_detections"): 30,
    ("cfg/time_tresholds.toml", "idle"): 3.0,
    ("cfg/time_tresholds.toml", "super"): 0.15,
    ("cfg/time_tresholds.toml", "hypercharge"): 0.15,
    ("cfg/time_tresholds.toml", "gadget"): 0.15,
    ("cfg/time_tresholds.toml", "wall_detection"): 0.15,
    ("cfg/time_tresholds.toml", "no_detection_proceed"): 8.0,
    ("cfg/time_tresholds.toml", "check_if_brawl_stars_crashed"): 10,

    # buttons_config.toml
    ("cfg/buttons_config.toml", "idle_reconnect"): [100, 100],
    ("cfg/buttons_config.toml", "brawlers_menu"): [100, 100],
    ("cfg/buttons_config.toml", "select_brawler"): [960, 540],
}


def get_config(path: str, key: str, default: Any = None, expected_type: type = None) -> Any:
    """
    Load config and return value for key, with fallback to default.
    Checks IRIS_* env vars first, then TOML file, then CONFIG_DEFAULTS.
    """
    load_env_file()

    env_value = get_env_override(path, key)
    if env_value is not None:
        return env_value

    try:
        config = load_toml_as_dict(path)
        if key in config:
            value = config[key]
            if expected_type is not None and not isinstance(value, expected_type):
                logger.warning(f"Config {path}: key '{key}' has wrong type (expected {expected_type.__name__}, got {type(value).__name__}). Using default.")
                return default
            return value
    except Exception as e:
        logger.warning(f"Config {path}: error loading: {e}")

    # Fallback to CONFIG_DEFAULTS
    fallback = CONFIG_DEFAULTS.get((path, key), default)
    logger.warning(f"Config {path}: key '{key}' not found, using default: {fallback}")
    return fallback

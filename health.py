from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import shutil
from pathlib import Path
from typing import Any

import toml

from config_loader import CONFIG_DEFAULTS
from runtime_paths import get_runtime_dir
from utils import resolve_project_path


CONFIG_FILES = [
    "cfg/general_config.toml",
    "cfg/bot_config.toml",
    "cfg/time_tresholds.toml",
    "cfg/buttons_config.toml",
    "cfg/webhook_config.toml",
    "cfg/debug_settings.toml",
    "cfg/login.toml",
    "cfg/lobby_config.toml",
]

PYTHON_MODULES = [
    "cv2",
    "numpy",
    "onnxruntime",
    "PIL",
    "flask",
    "pandas",
    "adbutils",
    "av",
    "easyocr",
]

REQUIRED_MODELS = [
    "mainInGameModel.onnx",
    "tileDetector.onnx",
    "closeTileDetector.onnx",
]

REQUIRED_EASYOCR_MODELS = [
    "craft_mlt_25k.pth",
    "english_g2.pth",
]

LEGACY_OPTIONAL_DEFAULTS = {
    ("cfg/general_config.toml", "bs_package_name"),
    ("cfg/general_config.toml", "process_every_n_frames"),
    ("cfg/bot_config.toml", "re_apply_movement"),
}


def _check(ok: bool, name: str, message: str, level: str = "error") -> dict[str, Any]:
    return {
        "ok": bool(ok),
        "name": name,
        "message": message,
        "level": "ok" if ok else level,
    }


def validate_macos() -> list[dict[str, Any]]:
    is_macos = platform.system() == "Darwin"
    checks = [
        _check(
            is_macos,
            "platform:macos",
            f"macOS detected ({platform.machine()})." if is_macos else "IrisAI supports macOS only.",
        )
    ]
    if is_macos:
        swiftc = shutil.which("swiftc")
        checks.append(_check(
            bool(swiftc),
            "platform:swiftc",
            f"Swift compiler found: {swiftc}" if swiftc else "Swift compiler missing; install Xcode Command Line Tools.",
            level="warning",
        ))
    return checks


def validate_config_files() -> list[dict[str, Any]]:
    checks = []
    for config_path in CONFIG_FILES:
        path = resolve_project_path(config_path)
        if not path.exists():
            checks.append(_check(False, config_path, "Missing config file. Code defaults may be used."))
            continue
        try:
            data = toml.load(path)
        except Exception as exc:
            checks.append(_check(False, config_path, f"Invalid TOML: {exc}"))
            continue
        missing_defaults = [
            key for file_path, key in CONFIG_DEFAULTS
            if file_path == config_path
            and key not in data
            and (file_path, key) not in LEGACY_OPTIONAL_DEFAULTS
        ]
        if missing_defaults:
            checks.append(_check(
                False,
                config_path,
                f"Missing keys using defaults: {', '.join(missing_defaults)}",
                level="warning",
            ))
        else:
            checks.append(_check(True, config_path, "Config file is readable."))
        if config_path == "cfg/general_config.toml":
            inference_mode = str(data.get("cpu_or_gpu", "auto")).strip().lower()
            checks.append(_check(
                inference_mode in {"auto", "coreml", "cpu"},
                "config:cpu_or_gpu",
                f"macOS inference mode: {inference_mode}."
                if inference_mode in {"auto", "coreml", "cpu"}
                else "cpu_or_gpu must be auto, coreml, or cpu.",
            ))
    return checks


def validate_runtime_dir() -> list[dict[str, Any]]:
    runtime_dir = get_runtime_dir()
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        probe = runtime_dir / ".write-test"
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return [_check(True, "runtime_dir", f"Runtime data directory is writable: {runtime_dir}")]
    except Exception as exc:
        return [_check(False, "runtime_dir", f"Runtime data directory is not writable: {runtime_dir} ({exc})")]


def validate_python_modules() -> list[dict[str, Any]]:
    checks = []
    for module_name in PYTHON_MODULES:
        found = importlib.util.find_spec(module_name) is not None
        checks.append(_check(
            found,
            f"python:{module_name}",
            "Installed." if found else "Missing Python dependency.",
            level="warning" if module_name in {"easyocr", "adbutils", "av"} else "error",
        ))
    if importlib.util.find_spec("cv2") and importlib.util.find_spec("av"):
        checks.append(_check(
            True,
            "python:cv2+av",
            "Both OpenCV and PyAV are installed. If macOS prints duplicate AVFoundation warnings, pin compatible wheel versions.",
            level="ok",
        ))
    return checks


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_models() -> list[dict[str, Any]]:
    checks = []
    models_dir = resolve_project_path("models")
    manifest_path = models_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            checks.append(_check(True, "models:manifest", "Model manifest is readable."))
        except Exception as exc:
            checks.append(_check(False, "models:manifest", f"Invalid manifest JSON: {exc}"))
    else:
        checks.append(_check(False, "models:manifest", "No model manifest found.", level="warning"))

    for model_name in REQUIRED_MODELS:
        model_path = models_dir / model_name
        if not model_path.exists():
            checks.append(_check(False, f"model:{model_name}", "Missing ONNX model."))
            continue
        expected_hash = manifest.get(model_name, {}).get("sha256") if isinstance(manifest.get(model_name), dict) else None
        if expected_hash:
            actual_hash = _sha256(model_path)
            checks.append(_check(
                actual_hash == expected_hash,
                f"model:{model_name}",
                "Model hash is valid." if actual_hash == expected_hash else "Model hash does not match manifest.",
            ))
        else:
            checks.append(_check(True, f"model:{model_name}", "Model file exists; no hash configured."))

    easyocr_dir = models_dir / "easyocr"
    for model_name in REQUIRED_EASYOCR_MODELS:
        path = easyocr_dir / model_name
        checks.append(_check(
            path.exists(),
            f"easyocr:{model_name}",
            "EasyOCR model exists." if path.exists() else "Missing EasyOCR model.",
            level="warning",
        ))
    return checks


def validate_adb() -> list[dict[str, Any]]:
    adb_path = shutil.which("adb")
    return [_check(
        bool(adb_path),
        "adb",
        f"ADB found: {adb_path}" if adb_path else "ADB not found in PATH.",
        level="warning",
    )]


def get_health_report(include_optional=True) -> dict[str, Any]:
    checks = []
    checks.extend(validate_macos())
    checks.extend(validate_runtime_dir())
    checks.extend(validate_config_files())
    checks.extend(validate_models())
    if include_optional:
        checks.extend(validate_python_modules())
        checks.extend(validate_adb())

    error_count = sum(1 for item in checks if not item["ok"] and item["level"] == "error")
    warning_count = sum(1 for item in checks if not item["ok"] and item["level"] == "warning")
    status = "error" if error_count else "warning" if warning_count else "ok"
    return {
        "ok": error_count == 0,
        "status": status,
        "error_count": error_count,
        "warning_count": warning_count,
        "checks": checks,
    }

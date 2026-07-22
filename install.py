#!/usr/bin/env python3
"""One-shot macOS installer for IrisAI."""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def detect_platform():
    system = platform.system()
    machine = platform.machine()
    if system != "Darwin":
        raise RuntimeError("IrisAI supports macOS only.")
    if machine in ("arm64", "aarch64"):
        return "macos_arm"
    return "macos_intel"


def detect_gpu():
    detect_platform()
    try:
        import torch
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "coreml"
    except ImportError:
        pass
    return "cpu"


def install_deps(gpu_profile, dry_run=False):
    print(f"\nInstalling dependencies ({gpu_profile} profile)...")

    base = [
        "opencv-python", "numpy", "requests", "toml", "pillow",
        "discord.py", "packaging",
    ]

    extras = ["torch", "onnxruntime"]

    full = [
        "easyocr", "adbutils", "av", "Flask", "pandas",
        "pycryptodome", "aiohttp",
    ]

    all_deps = base + extras + full

    for dep in all_deps:
        if dry_run:
            print(f"  Would install {dep}")
            continue
        print(f"  Installing {dep}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", dep],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print("  Dependency plan complete." if dry_run else "  Dependencies installed.")


def download_models(dry_run=False):
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    manifest_path = models_dir / "manifest.json"
    if not manifest_path.exists():
        print("  No model manifest found — ONNX models will be downloaded on first use.")
        print("  ONNX models should be placed in models/ manually or via iris update-models.")
        return

    import json
    import hashlib

    manifest = json.loads(manifest_path.read_text())
    for model_name, model_info in manifest.items():
        model_path = models_dir / model_name
        if model_path.exists():
            if "sha256" in model_info:
                current_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
                if current_hash == model_info["sha256"]:
                    print(f"  {model_name}: OK")
                    continue
                print(f"  {model_name}: hash mismatch, re-downloading...")
            else:
                print(f"  {model_name}: exists, skipping")
                continue

        url = model_info.get("url")
        if not url:
            print(f"  {model_name}: no URL in manifest, skipping")
            continue

        if dry_run:
            print(f"  Would download {model_name} from {url}")
            continue

        print(f"  Downloading {model_name}...")
        try:
            import requests
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            model_path.write_bytes(response.content)
            print(f"  {model_name}: downloaded ({len(response.content)//1024//1024} MB)")
        except Exception as e:
            print(f"  {model_name}: download failed ({e})")


def download_easyocr_models(dry_run=False):
    """Download EasyOCR model files (craft_mlt_25k.pth, english_g2.pth)."""
    easyocr_dir = Path("models/easyocr")
    easyocr_dir.mkdir(parents=True, exist_ok=True)

    # EasyOCR model files from our own release
    easyocr_models = {
        "craft_mlt_25k.pth": "https://github.com/rarebinary/IrisAI/releases/download/easyocr-v1/craft_mlt_25k.pth",
        "english_g2.pth": "https://github.com/rarebinary/IrisAI/releases/download/easyocr-v1/english_g2.pth",
        "latin_g2.pth": "https://github.com/rarebinary/IrisAI/releases/download/easyocr-v1/latin_g2.pth",
    }

    print("\nDownloading EasyOCR models...")
    for name, url in easyocr_models.items():
        model_path = easyocr_dir / name
        if model_path.exists():
            print(f"  {name}: already exists, skipping")
            continue
        if dry_run:
            print(f"  Would download {name} from {url}")
            continue
        print(f"  Downloading {name}...")
        try:
            import requests
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            model_path.write_bytes(response.content)
            print(f"  {name}: downloaded ({len(response.content)//1024//1024} MB)")
        except Exception as e:
            print(f"  {name}: download failed ({e})")


def verify_adb():
    adb_path = shutil.which("adb")
    if adb_path:
        print(f"  ADB found: {adb_path}")
        return True
    else:
        print("  ADB not found in PATH.")
        detect_platform()
        print("  Install with: brew install android-platform-tools")
        return False


def create_env_file(dry_run=False):
    env_path = Path(".env")
    if env_path.exists():
        print("  .env already exists, skipping")
        return

    env_content = """# IrisAI Configuration
# Uncomment and fill in the values you want to use.

# Discord (required for bot slash commands)
# IRIS_DISCORD_BOT_TOKEN=
# IRIS_DISCORD_USER_ID=
# IRIS_DISCORD_GUILD_ID=
# IRIS_DISCORD_WEBHOOK_URL=

# Telegram (optional)
# IRIS_TELEGRAM_BOT_TOKEN=
# IRIS_TELEGRAM_CHAT_ID=

# API Cloud (optional)
# IRIS_API_KEY=
# IRIS_API_BASE_URL=https://api.iris.example.com
"""
    if dry_run:
        print("  Would create .env with template")
        return
    env_path.write_text(env_content)
    print("  .env created with template")


def run_health_check():
    print("\nRunning health check...")
    try:
        from health import get_health_report
        report = get_health_report()
    except Exception as exc:
        print(f"  Health check failed to run: {exc}")
        return

    print(f"  Status: {report['status']} ({report['error_count']} errors, {report['warning_count']} warnings)")
    for check in report["checks"]:
        if check["ok"]:
            continue
        print(f"  - {check['level'].upper()} {check['name']}: {check['message']}")


def main():
    parser = argparse.ArgumentParser(description="Install IrisAI")
    parser.add_argument("--cpu", action="store_true", help="Force CPU-only installation")
    parser.add_argument("--coreml", action="store_true", help="Force CoreML installation (macOS)")
    parser.add_argument("--dev", action="store_true", help="Dev mode (pip install -e .)")
    parser.add_argument("--no-adb", action="store_true", help="Skip ADB verification")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without installing or downloading")
    args = parser.parse_args()

    print("=" * 50)
    print("  IrisAI Installer")
    print("=" * 50)

    plat = detect_platform()
    print(f"\nPlatform: {plat}")

    if args.cpu:
        gpu_profile = "cpu"
    elif args.coreml:
        gpu_profile = "coreml"
    else:
        gpu_profile = detect_gpu()

    print(f"GPU profile: {gpu_profile}")

    install_deps(gpu_profile, dry_run=args.dry_run)

    if args.dev:
        print("\nInstalling in development mode...")
        if args.dry_run:
            print("  Would run pip install -e .")
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])

    print("\nChecking models...")
    download_models(dry_run=args.dry_run)
    download_easyocr_models(dry_run=args.dry_run)

    if not args.no_adb:
        print("\nVerifying ADB...")
        verify_adb()

    print("\nCreating .env...")
    create_env_file(dry_run=args.dry_run)
    run_health_check()

    print("\n" + "=" * 50)
    print("  Dry run complete!" if args.dry_run else "  Installation complete!")
    if not args.dry_run:
        print("  Run: python main.py")
    print("=" * 50)


if __name__ == "__main__":
    main()

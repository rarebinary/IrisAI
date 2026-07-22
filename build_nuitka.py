#!/usr/bin/env python3
"""
build_nuitka.py — Build standalone macOS .app bundle via Nuitka.

Usage:
    python build_nuitka.py

Requires:
    pip install nuitka
    (macOS only; cross-compilation not supported)
"""
import platform
import subprocess
import sys


def main():
    if platform.system() != "Darwin":
        print("IrisAI builds are supported on macOS only.")
        sys.exit(2)
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--follow-imports",
        "--include-package=onnxruntime",
        "--include-package=easyocr",
        "--include-package=flask",
        "--include-package=discord",
        "--include-package=pandas",
        "--include-package=av",
        "--include-package=adbutils",
        "--include-data-dir=images=images",
        "--include-data-dir=cfg=cfg",
        "--include-data-dir=playstyles=playstyles",
        "--include-data-dir=models=models",
        "--include-data-dir=templates=templates",
        "--include-data-dir=static=static",
        "--include-data-dir=sounds=sounds",
        "--include-data-dir=native=native",
        "--macos-create-app-bundle",
        "--macos-app-name=IrisAI",
        "--macos-app-version=1.0.0",
        "--output-dir=dist",
        "--no-deployment-flag=self-execution",
        "main.py"
    ]
    
    print("Building IrisAI.app with Nuitka...")
    print(f"Command: {' '.join(cmd)}")
    print("This may take several minutes.")
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild complete!")
        print("App bundle: dist/IrisAI.app")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("\nNuitka not found. Install with: pip install nuitka")
        sys.exit(1)


if __name__ == "__main__":
    main()

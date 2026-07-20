"""Setup script for IrisAI."""
from setuptools import setup, find_packages

setup(
    name="IrisAI",
    version="1.0.0",
    packages=find_packages(exclude=["api", "cfg", "images", "models"]),
    python_requires=">=3.11",
    install_requires=[
        "opencv-python>=4.11",
        "numpy>=2.3",
        "requests>=2.32",
        "toml>=0.10",
        "pillow>=11.2.1",
        "discord.py>=2.7",
        "packaging>=25.0",
    ],
    extras_require={
        "cpu": ["torch", "onnxruntime"],
        "coreml": ["torch", "onnxruntime-silicon"],
        "full": [
            "easyocr>=1.7",
            "adbutils>=2.12",
            "av>=12.3",
            "Flask>=3.1",
            "pandas>=3.0",
            "pycryptodome>=3.21",
            "aiohttp>=3.13",
        ],
    },
    entry_points={
        "console_scripts": [
            "iris=main:cli_entry_point",
        ],
    },
)

import os
import threading
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME_DIR = PROJECT_ROOT / ".iris_runtime"
_prune_lock = threading.Lock()


def get_runtime_dir() -> Path:
    configured = os.environ.get("IRIS_RUNTIME_DIR", "").strip()
    return Path(configured).expanduser().resolve() if configured else DEFAULT_RUNTIME_DIR


def runtime_path(*parts, create_parent=True) -> Path:
    path = get_runtime_dir().joinpath(*parts)
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def first_existing_runtime_path(runtime_parts, legacy_path) -> Path:
    runtime_file = runtime_path(*runtime_parts, create_parent=False)
    if runtime_file.exists():
        return runtime_file
    legacy = PROJECT_ROOT / legacy_path
    return legacy if legacy.exists() else runtime_file


def prune_runtime_files(directory, patterns, max_files=100, max_bytes=500 * 1024 * 1024):
    directory = Path(directory)
    if not directory.exists():
        return 0, 0

    with _prune_lock:
        candidates = set()
        for pattern in patterns:
            candidates.update(path for path in directory.rglob(pattern) if path.is_file())

        files = []
        for path in candidates:
            try:
                stat = path.stat()
            except OSError:
                continue
            files.append((stat.st_mtime_ns, path, stat.st_size))
        files.sort(reverse=True)

        kept_count = 0
        kept_bytes = 0
        deleted_count = 0
        deleted_bytes = 0
        for _, path, size in files:
            count_fits = max_files <= 0 or kept_count < max_files
            size_fits = max_bytes <= 0 or kept_bytes + size <= max_bytes
            keep = kept_count == 0 or (count_fits and size_fits)
            if keep:
                kept_count += 1
                kept_bytes += size
                continue
            try:
                path.unlink()
            except OSError:
                continue
            deleted_count += 1
            deleted_bytes += size

        return deleted_count, deleted_bytes

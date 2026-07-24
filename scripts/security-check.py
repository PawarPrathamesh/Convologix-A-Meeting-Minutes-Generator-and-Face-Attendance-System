from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PREFIXES = (
    ".idea/",
    ".ipynb_checkpoints/",
    "Dataset/",
    "Testing/",
    "Test Accuracy/",
    "Extracted Audio/",
    "Minutes of Meeting/",
    "Video ScreenShots/",
    "Trained Model/",
    "images/test1/",
    "data/",
    "__pycache__/",
)
FORBIDDEN_NAMES = {
    "Accuracy Graph.png",
    ".gitignore.txt",
    "Mail App Password.txt",
    "ResultsMap.pkl",
}
FORBIDDEN_SUFFIXES = {
    ".h5",
    ".onnx",
    ".pyc",
    ".pkl",
}
SECRET_PATTERNS = (
    re.compile(r"convologix11@gmail\.com", re.IGNORECASE),
    re.compile("".join(("ihfmw", "fpbot", "kkkdcd")), re.IGNORECASE),
    re.compile(r"HUGGINGFACE_TOKEN\s*=\s*hf_[A-Za-z0-9_]+"),
    re.compile(r"HF_TOKEN\s*=\s*hf_[A-Za-z0-9_]+"),
)
TEXT_SUFFIXES = {
    ".css",
    ".dockerignore",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yml",
    ".yaml",
}


def tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-files", "-z"], cwd=ROOT)
    return [item for item in output.decode("utf-8", errors="replace").split("\0") if item]


def is_forbidden_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    path_obj = Path(normalized)
    return (
        normalized.startswith(FORBIDDEN_PREFIXES)
        or path_obj.name in FORBIDDEN_NAMES
        or path_obj.suffix.lower() in FORBIDDEN_SUFFIXES
        or "__pycache__/" in normalized
    )


def should_scan_text(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.stat().st_size > 1_000_000:
        return False
    suffixes = {suffix.lower() for suffix in path.suffixes}
    return bool(suffixes & TEXT_SUFFIXES) or path.name in {".gitignore", ".dockerignore"}


def main() -> int:
    failures: list[str] = []
    files = tracked_files()

    forbidden = [path for path in files if is_forbidden_path(path)]
    if forbidden:
        failures.append("Forbidden tracked release artifacts:\n" + "\n".join(f"  - {path}" for path in forbidden))

    for relative_path in files:
        path = ROOT / relative_path
        if not should_scan_text(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"Potential secret pattern in {relative_path}: {pattern.pattern}")

    if failures:
        print("Security check failed:", file=sys.stderr)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("Security check passed: release tree has no tracked private artifacts or known secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

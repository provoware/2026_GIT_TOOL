import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from src.records.record_updater import main

    return int(main())


if __name__ == "__main__":
    raise SystemExit(run())

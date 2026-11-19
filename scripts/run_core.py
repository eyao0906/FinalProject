from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the required vanilla and Asian core grid.")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "core")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "stat906cv.experiments",
            "--config",
            str(ROOT / "configs" / "core.yaml"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

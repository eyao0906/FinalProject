from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest and save machine-readable test outcomes.")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "validation")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    junit = output / "pytest.xml"
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", f"--junitxml={junit}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    (output / "pytest_output.txt").write_text(
        process.stdout + process.stderr, encoding="utf-8"
    )
    suite = ET.parse(junit).getroot()
    suites = list(suite.iter("testsuite"))
    result = {
        "return_code": process.returncode,
        "tests": sum(int(item.attrib.get("tests", 0)) for item in suites),
        "failures": sum(int(item.attrib.get("failures", 0)) for item in suites),
        "errors": sum(int(item.attrib.get("errors", 0)) for item in suites),
        "skipped": sum(int(item.attrib.get("skipped", 0)) for item in suites),
        "junit_file": str(junit),
    }
    (output / "test_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="", file=sys.stderr)
    print(json.dumps(result, indent=2))
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())

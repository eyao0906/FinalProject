from __future__ import annotations

import argparse
from pathlib import Path

from stat906cv.experiments import revalidate_saved_results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Revalidate saved experiment rows without rerunning pricing."
    )
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    validation = revalidate_saved_results(args.result_dir)
    destination = args.result_dir / "validation.json"
    print(f"Validation: {'PASS' if validation['passed'] else 'FAIL'} ({destination})")
    return 0 if validation["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

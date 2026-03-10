from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a WarpLab optimization workflow.")
    parser.add_argument("project", help="Path to a WarpLab project directory")
    parser.add_argument(
        "--root-dir",
        default=".",
        help="Repository root containing projects/, runs/, reports/, and db/",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=None,
        help="Override the number of candidates to evaluate",
    )
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Skip baseline profiling with Nsight Compute",
    )
    args = parser.parse_args()

    result = run_project(
        Path(args.project),
        Path(args.root_dir),
        candidate_count=args.candidate_count,
        profile_baseline=not args.no_profile,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cloud import collect_runtime_diagnostics, format_runtime_report
from .kaggle_api import format_kaggle_doctor_report, kaggle_doctor
from .kaggle_kernel import write_kaggle_kernel_package, write_kaggle_project_package
from .runner import run_project


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "doctor":
        diagnostics = collect_runtime_diagnostics()
        print(format_runtime_report(diagnostics))
        return 0
    if argv and argv[0] == "kaggle-doctor":
        report = kaggle_doctor(Path.cwd())
        print(format_kaggle_doctor_report(report))
        return 0
    if argv and argv[0] == "kaggle-package":
        parser = argparse.ArgumentParser(description="Create a Kaggle kernel package for WarpLab validation.")
        parser.add_argument("--output-dir", default="build/kaggle-validation")
        parser.add_argument("--username", default=None)
        parser.add_argument("--title", default="WarpLab Kaggle Runtime Validation")
        parser.add_argument("--slug", default=None)
        parser.add_argument("--repo-dir", default="warplab")
        parser.add_argument("--repo-url", default=None)
        parser.add_argument("--public", action="store_true")
        args = parser.parse_args(argv[1:])

        from .kaggle_api import kaggle_credentials

        username = args.username or kaggle_credentials(Path.cwd()).get("username")
        if not username:
            raise SystemExit("KAGGLE_USERNAME is required for kaggle-package.")

        path = write_kaggle_kernel_package(
            Path(args.output_dir),
            username=username,
            title=args.title,
            slug=args.slug,
            repo_dir=args.repo_dir,
            repo_url=args.repo_url,
            is_private=not args.public,
        )
        print(json.dumps({"package_dir": str(path.resolve())}, indent=2))
        return 0
    if argv and argv[0] == "kaggle-project-package":
        parser = argparse.ArgumentParser(description="Create a Kaggle kernel package that runs a WarpLab project.")
        parser.add_argument("--output-dir", default="build/kaggle-project")
        parser.add_argument("--project", default="projects/saxpy")
        parser.add_argument("--username", default=None)
        parser.add_argument("--title", default="WarpLab SAXPY Kaggle Run")
        parser.add_argument("--slug", default=None)
        parser.add_argument("--repo-dir", default="warplab")
        parser.add_argument("--repo-url", default=None)
        parser.add_argument("--candidate-count", type=int, default=8)
        parser.add_argument("--no-profile", action="store_true")
        parser.add_argument("--public", action="store_true")
        args = parser.parse_args(argv[1:])

        from .kaggle_api import kaggle_credentials

        username = args.username or kaggle_credentials(Path.cwd()).get("username")
        if not username:
            raise SystemExit("KAGGLE_USERNAME is required for kaggle-project-package.")

        path = write_kaggle_project_package(
            Path(args.output_dir),
            project=args.project,
            username=username,
            title=args.title,
            slug=args.slug,
            repo_dir=args.repo_dir,
            repo_url=args.repo_url,
            candidate_count=args.candidate_count,
            profile=not args.no_profile,
            is_private=not args.public,
        )
        print(json.dumps({"package_dir": str(path.resolve())}, indent=2))
        return 0

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

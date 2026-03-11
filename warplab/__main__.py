from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cloud import collect_runtime_diagnostics, format_runtime_report
from .kaggle_api import format_kaggle_doctor_report, kaggle_doctor, resolve_kaggle_username
from .kaggle_kernel import write_kaggle_kernel_package, write_kaggle_project_package
from .runner import run_project


def main() -> int:
    argv = sys.argv[1:]
    known_commands = {"run", "doctor", "kaggle-doctor", "kaggle-package", "kaggle-project-package"}
    if argv and argv[0] not in known_commands and argv[0] not in {"-h", "--help"}:
        argv = ["run", *argv]

    parser = argparse.ArgumentParser(description="WarpLab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a WarpLab optimization workflow.")
    run_parser.add_argument("project", help="Path to a WarpLab project directory")
    run_parser.add_argument(
        "--root-dir",
        default=".",
        help="Repository root containing projects/, runs/, reports/, and db/",
    )
    run_parser.add_argument(
        "--candidate-count",
        type=int,
        default=None,
        help="Override the number of candidates to evaluate",
    )
    run_parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Skip baseline profiling with Nsight Compute",
    )

    subparsers.add_parser("doctor", help="Print local runtime diagnostics.")
    subparsers.add_parser("kaggle-doctor", help="Verify Kaggle CLI authentication and resolve the username.")

    kaggle_package_parser = subparsers.add_parser(
        "kaggle-package",
        help="Create a Kaggle kernel package for WarpLab runtime validation.",
    )
    kaggle_package_parser.add_argument("--output-dir", default="build/kaggle-validation")
    kaggle_package_parser.add_argument("--username", default=None)
    kaggle_package_parser.add_argument("--title", default="WarpLab Kaggle Runtime Validation")
    kaggle_package_parser.add_argument("--slug", default=None)
    kaggle_package_parser.add_argument("--repo-dir", default="warplab")
    kaggle_package_parser.add_argument("--repo-url", default=None)
    kaggle_package_parser.add_argument("--public", action="store_true")

    kaggle_project_parser = subparsers.add_parser(
        "kaggle-project-package",
        help="Create a Kaggle kernel package that runs a WarpLab project.",
    )
    kaggle_project_parser.add_argument("--output-dir", default="build/kaggle-project")
    kaggle_project_parser.add_argument("--project", default="projects/saxpy")
    kaggle_project_parser.add_argument("--username", default=None)
    kaggle_project_parser.add_argument("--title", default="WarpLab SAXPY Kaggle Run")
    kaggle_project_parser.add_argument("--slug", default=None)
    kaggle_project_parser.add_argument("--repo-dir", default="warplab")
    kaggle_project_parser.add_argument("--repo-url", default=None)
    kaggle_project_parser.add_argument("--candidate-count", type=int, default=8)
    kaggle_project_parser.add_argument("--no-profile", action="store_true")
    kaggle_project_parser.add_argument("--public", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "doctor":
        diagnostics = collect_runtime_diagnostics()
        print(format_runtime_report(diagnostics))
        return 0

    if args.command == "kaggle-doctor":
        report = kaggle_doctor(Path.cwd())
        print(format_kaggle_doctor_report(report))
        return 0

    if args.command == "kaggle-package":
        username = args.username or resolve_kaggle_username(Path.cwd())
        if not username:
            raise SystemExit("Could not resolve Kaggle username. Set KAGGLE_API_TOKEN or KAGGLE_USERNAME/KAGGLE_KEY, then rerun `warplab kaggle-doctor`.")

        path = write_kaggle_kernel_package(
            Path(args.output_dir),
            username=username,
            title=args.title,
            slug=args.slug,
            repo_dir=args.repo_dir,
            repo_url=args.repo_url,
            is_private=not args.public,
        )
        slug = args.slug or " ".join(args.title.strip().lower().split()).replace(" ", "-")
        print(
            json.dumps(
                {
                    "package_dir": str(path.resolve()),
                    "kernel_ref": f"{username}/{slug}",
                    "slug": slug,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "kaggle-project-package":
        username = args.username or resolve_kaggle_username(Path.cwd())
        if not username:
            raise SystemExit("Could not resolve Kaggle username. Set KAGGLE_API_TOKEN or KAGGLE_USERNAME/KAGGLE_KEY, then rerun `warplab kaggle-doctor`.")

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
        slug = args.slug or " ".join(args.title.strip().lower().split()).replace(" ", "-")
        print(
            json.dumps(
                {
                    "package_dir": str(path.resolve()),
                    "kernel_ref": f"{username}/{slug}",
                    "slug": slug,
                },
                indent=2,
            )
        )
        return 0

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

import json
import subprocess
import sys
import unittest
import tempfile
from pathlib import Path
from unittest import mock


class CoreTests(unittest.TestCase):
    def test_render_command_requires_all_placeholders(self):
        from warplab.execution import render_command

        with self.assertRaises(ValueError) as exc:
            render_command("{artifact} --size {size}", artifact="./bench")
        self.assertIn("size", str(exc.exception))

    def test_constraints_are_evaluated_safely(self):
        try:
            from warplab.search import is_valid_config
        except ModuleNotFoundError as exc:
            self.skipTest(f"Dependency missing for search module: {exc}")

        self.assertTrue(
            is_valid_config({"block_size": 128, "vector_width": 4}, ["block_size % 32 == 0"])
        )
        self.assertFalse(
            is_valid_config({"block_size": 130, "vector_width": 4}, ["block_size % 32 == 0"])
        )
        self.assertFalse(is_valid_config({"block_size": 128}, ["unknown_param == 1"]))

    def test_random_candidates_are_deduplicated(self):
        try:
            from warplab.models import ProjectConfig
            from warplab.search import generate_local_refinements, generate_random_candidates
        except ModuleNotFoundError as exc:
            self.skipTest(f"Dependency missing for candidate generation: {exc}")

        config = ProjectConfig(
            name="test",
            description="test",
            build={"compile_kernel": "true", "compile_validate": "true"},
            run={"benchmark": "{artifact}", "validate": "{artifact}"},
            input={"size": 1},
            objective={"metric": "latency_ms", "direction": "minimize"},
            search_space={"block_size": [64], "vector_width": [1, 2]},
            constraints=["block_size % 32 == 0"],
            validation={"atol": 1e-6, "rtol": 1e-5},
            budget={"max_experiments": 10, "warmup_runs": 1, "timed_runs": 1},
        )

        candidates = generate_random_candidates(config, 10)
        unique = {tuple(sorted(candidate.params.items())) for candidate in candidates}
        self.assertEqual(len(candidates), len(unique))

        refinements = generate_local_refinements(candidates[:1], config, 3)
        for refinement in refinements:
            self.assertTrue(refinement.params)

    def test_memory_run_lifecycle_and_report_generation(self):
        try:
            from warplab.memory import Memory
            from warplab.report import generate_markdown_report, write_json_summary
        except ModuleNotFoundError as exc:
            self.skipTest(f"Dependency missing for memory/report modules: {exc}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "db" / "warplab.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            memory = Memory(db_path)

            run_id = "run123"
            memory.insert_run(
                run_id,
                "saxpy",
                {
                    "timestamp": "2026-03-10T00:00:00",
                    "gpu_name": "GPU",
                    "compute_capability": "8.0",
                    "cuda_version": "12.4",
                    "driver_version": "550",
                    "git_commit": "abc123",
                },
                {"metric": "latency_ms", "direction": "minimize"},
            )
            memory.finalize_run(run_id, "completed")

            report_path = generate_markdown_report(
                run_id,
                "saxpy",
                {
                    "timestamp": "2026-03-10T00:00:00",
                    "gpu_name": "GPU",
                    "compute_capability": "8.0",
                    "cuda_version": "12.4",
                    "os": "Linux",
                },
                {"latency_ms": 1.23, "cv": 0.01},
                {
                    "config": {"params": {"block_size": 256}},
                    "latency_ms": 1.0,
                    "speedup": 1.23,
                    "score": 1.2,
                    "cv": 0.02,
                },
                {
                    "diagnosis": "Balanced",
                    "explanation": "Looks fine",
                    "suggestions": "Keep iterating",
                },
                tmp_path / "reports",
            )
            self.assertTrue(report_path.exists())
            summary_path = write_json_summary(run_id, {"run_id": run_id}, tmp_path / "reports")
            self.assertTrue(summary_path.exists())

    def test_benchmark_uses_explicit_budget_values(self):
        from warplab.benchmark import run_benchmark
        from warplab.execution import CommandResult

        captured = {}

        def fake_run_command(command, cwd, timeout_s=None):
            captured["command"] = command
            return CommandResult(
                success=True,
                command=command,
                cwd=str(cwd),
                returncode=0,
                stdout='{"latency_ms": 1.0}\n{"latency_ms": 1.1}\n',
                stderr="",
                duration_s=0.01,
            )

        with mock.patch("warplab.benchmark.run_command", side_effect=fake_run_command):
            run_benchmark(
                Path("/tmp/fake-bench"),
                "{artifact} --warmups {warmups} --repeats {repeats}",
                warmup_runs=1,
                timed_runs=2,
                cwd=Path("/tmp"),
                extra_context={"warmups": 99, "repeats": 99},
            )

        self.assertIn("--warmups 1", captured["command"])
        self.assertIn("--repeats 2", captured["command"])

    def test_cloud_runtime_helpers(self):
        from warplab.cloud import (
            collect_runtime_diagnostics,
            notebook_bootstrap_snippet,
            project_results_cell_snippet,
            project_run_cell_snippet,
            runtime_warnings,
            validation_cell_snippet,
        )

        diagnostics = collect_runtime_diagnostics()
        self.assertIn("environment", diagnostics)
        self.assertIn("tools", diagnostics)
        self.assertIsInstance(runtime_warnings(diagnostics), list)
        self.assertIn("uv sync --dev", notebook_bootstrap_snippet())
        self.assertIn("git clone", notebook_bootstrap_snippet("https://github.com/example/repo.git"))
        self.assertIn("collect_runtime_diagnostics", validation_cell_snippet())
        self.assertIn("sys.path.insert(0, str(ROOT_DIR))", validation_cell_snippet())
        self.assertIn("uv', 'run', 'warplab'", project_run_cell_snippet())
        self.assertIn("WarpLab stderr:", project_run_cell_snippet())
        self.assertIn("plotly.express", project_results_cell_snippet())
        self.assertIn(
            "git', 'clone', '--depth', '1', 'https://github.com/example/repo.git'",
            validation_cell_snippet(repo_url="https://github.com/example/repo.git"),
        )

    def test_kaggle_env_loading(self):
        from warplab.kaggle_api import kaggle_credentials, load_dotenv, resolve_kaggle_username

        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text("KAGGLE_API_TOKEN=test-token\nKAGGLE_USERNAME=test-user\nKAGGLE_KEY=test-key\n")
            values = load_dotenv(env_path)
            self.assertEqual(values["KAGGLE_API_TOKEN"], "test-token")
            self.assertEqual(values["KAGGLE_USERNAME"], "test-user")
            self.assertEqual(values["KAGGLE_KEY"], "test-key")
            credentials = kaggle_credentials(Path(tmp_dir))
            self.assertEqual(credentials["api_token"], "test-token")
            self.assertEqual(resolve_kaggle_username(Path(tmp_dir)), "test-user")

    def test_kaggle_credentials_support_access_token_file(self):
        from warplab.kaggle_api import kaggle_credentials

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            kaggle_dir = tmp_path / ".kaggle"
            kaggle_dir.mkdir()
            (kaggle_dir / "access_token").write_text("token-from-file\n")
            with mock.patch("warplab.kaggle_api.Path.home", return_value=tmp_path):
                credentials = kaggle_credentials(tmp_path)
            self.assertEqual(credentials["api_token"], "token-from-file")

    def test_kaggle_kernel_package_generation(self):
        from warplab.kaggle_kernel import (
            discover_repo_url,
            kaggle_kernel_metadata,
            write_kaggle_project_package,
            write_kaggle_kernel_package,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            package_dir = write_kaggle_kernel_package(Path(tmp_dir), username="user123", slug="warp-test")
            metadata = json.loads((package_dir / "kernel-metadata.json").read_text())
            notebook = json.loads((package_dir / "warp-test.ipynb").read_text())
            self.assertEqual(metadata["id"], "user123/warp-test")
            self.assertTrue(metadata["enable_gpu"])
            self.assertEqual(metadata["kernel_type"], "notebook")
            self.assertTrue((package_dir / "warp-test.ipynb").exists())
            self.assertTrue((package_dir / "warplab" / "pyproject.toml").exists())
            self.assertTrue((package_dir / "warplab" / "warplab" / "__main__.py").exists())
            self.assertIn("git', 'clone', '--depth', '1'", "".join(notebook["cells"][1]["source"]))

        metadata = kaggle_kernel_metadata("user123", "warp-test", "Warp Test", "warp-test.ipynb")
        self.assertEqual(metadata["code_file"], "warp-test.ipynb")
        self.assertTrue(discover_repo_url())

        with tempfile.TemporaryDirectory() as tmp_dir:
            package_dir = write_kaggle_project_package(
                Path(tmp_dir),
                project="projects/saxpy",
                username="user123",
                slug="warp-saxpy",
            )
            notebook = json.loads((package_dir / "warp-saxpy.ipynb").read_text())
            combined_source = "".join("".join(cell["source"]) for cell in notebook["cells"])
            self.assertIn("projects/saxpy", combined_source)
            self.assertIn("uv', 'run', 'warplab'", combined_source)
            self.assertIn("summary['run_summary_path']", combined_source)

    def test_cli_help_lists_subcommands(self):
        result = subprocess.run(
            [sys.executable, "-m", "warplab", "--help"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("run", result.stdout)
        self.assertIn("doctor", result.stdout)
        self.assertIn("kaggle-doctor", result.stdout)
        self.assertIn("kaggle-project-package", result.stdout)


if __name__ == "__main__":
    unittest.main()

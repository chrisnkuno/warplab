import unittest
import tempfile
from pathlib import Path


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

    def test_cloud_runtime_helpers(self):
        from warplab.cloud import collect_runtime_diagnostics, notebook_bootstrap_snippet, runtime_warnings

        diagnostics = collect_runtime_diagnostics()
        self.assertIn("environment", diagnostics)
        self.assertIn("tools", diagnostics)
        self.assertIsInstance(runtime_warnings(diagnostics), list)
        self.assertIn("uv sync --dev", notebook_bootstrap_snippet())


if __name__ == "__main__":
    unittest.main()

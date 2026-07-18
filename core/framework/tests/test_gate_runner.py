"""Contrato neutral de gates para pre-push y CI."""

from __future__ import annotations

import json
import runpy
import shlex
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class GateRunnerTests(unittest.TestCase):
    def test_pre_push_and_ci_include_tests_and_release_without_recursion(self):
        registry = json.loads(
            (ROOT / ".specify/gates.json").read_text(encoding="utf-8")
        )
        by_scope = {"pre-push": [], "ci": [], "manual": []}
        for gate in registry["gates"]:
            command = shlex.split(gate["command"])
            self.assertTrue(command)
            scopes = [scope.strip() for scope in gate["scope"].split(",")]
            if {"pre-push", "ci"} & set(scopes):
                self.assertNotIn("scripts/validate.sh", command[0])
            for scope in scopes:
                by_scope.setdefault(scope.strip(), []).append(gate["id"])
        self.assertEqual(by_scope["pre-push"], by_scope["ci"])
        self.assertIn("TEST", by_scope["pre-push"])
        self.assertIn("CORE-RELEASE-SEAL", by_scope["pre-push"])
        self.assertEqual(by_scope["manual"], ["VALIDATE"])

    def test_scripts_delegate_to_neutral_runner(self):
        validate = (ROOT / "scripts/validate.sh").read_text(encoding="utf-8")
        ci = (ROOT / "scripts/ci.sh").read_text(encoding="utf-8")
        hook = (ROOT / "scripts/install-hooks.sh").read_text(encoding="utf-8")
        self.assertIn("scripts/run-gates.py\" --scope pre-push", validate)
        self.assertIn("scripts/run-gates.py\" --scope ci", ci)
        self.assertIn('pre_push_check.py', hook)

    def test_bitbucket_pipeline_delegates_only_to_canonical_ci_runner(self):
        pipeline = (ROOT / "bitbucket-pipelines.yml").read_text(encoding="utf-8")
        registry = json.loads(
            (ROOT / ".specify/gates.json").read_text(encoding="utf-8")
        )

        self.assertIn("image: python:3.11-bookworm", pipeline)
        self.assertIn("image: python:3.12-bookworm", pipeline)
        self.assertIn("image: python:3.13-bookworm", pipeline)
        self.assertIn("clone:\n  depth: full\n", pipeline)
        self.assertIn("pipelines:\n  default:\n", pipeline)
        self.assertNotIn("branches:", pipeline)
        self.assertEqual(pipeline.count("./scripts/ci.sh"), 3)
        self.assertIn(
            '- \'test "$BITBUCKET_COMMIT" = "$(git rev-parse HEAD)"\'\n',
            pipeline,
        )
        script_commands = [
            line.removeprefix("              - ")
            for line in pipeline.splitlines()
            if line.startswith("              - ")
        ]
        self.assertEqual(
            script_commands,
            [item for _ in range(3) for item in [
                '\'test "$BITBUCKET_COMMIT" = "$(git rev-parse HEAD)"\'',
                "./scripts/ci.sh",
            ]],
        )
        self.assertEqual(pipeline.count("- ./scripts/ci.sh\n"), 3)
        self.assertNotIn("scripts/run-gates.py", pipeline)
        self.assertNotIn("scripts/test.sh", pipeline)
        for gate in registry["gates"]:
            self.assertNotIn(gate["command"], pipeline)
        structure = runpy.run_path(
            str(ROOT / "tools/validation/monorepo_structure_check.py")
        )
        self.assertIn("bitbucket-pipelines.yml", structure["ALLOWED"])
        self.assertEqual(
            structure["REPOSITORY_INTEGRATIONS"], {"bitbucket-pipelines.yml"}
        )


if __name__ == "__main__":
    unittest.main()

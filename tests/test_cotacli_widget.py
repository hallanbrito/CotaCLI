"""Verifica o contrato que o plasmoide consome sem chamar serviços externos."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cotacli


class WidgetContractTests(unittest.TestCase):
    def test_snapshot_only_lists_installed_clis_and_separates_agy_groups(self):
        groups = {
            "agy-gemini": {"5h": {"remaining": 100.0, "reset": 1793300000},
                           "week": {"remaining": 90.6, "reset": 1793400000}},
            "agy-others": {"5h": {"remaining": 100.0, "reset": 1793300000},
                           "week": {"remaining": 100.0, "reset": 1793400000}},
        }
        with patch.object(cotacli, "find_cli", side_effect=lambda name: "/bin/true" if name in ("codex", "agy") else None), \
             patch.object(cotacli, "get_codex", return_value=({"5h": {"remaining": 66.0}}, "automático")), \
             patch.object(cotacli, "get_agy", return_value=(groups, "automático")):
            result = cotacli.snapshot()
        self.assertEqual(result["schema"], 1)
        self.assertEqual([item["id"] for item in result["providers"]],
                         ["codex", "agy-gemini", "agy-others"])
        self.assertEqual(result["providers"][1]["windows"]["week"]["remaining"], 90.6)

    def test_claude_installed_without_current_quota_is_hidden(self):
        with patch.object(cotacli, "find_cli", side_effect=lambda name: "/bin/true" if name == "claude" else None), \
             patch.object(cotacli, "get_claude", return_value=({}, "sem cota capturada")):
            self.assertEqual(cotacli.snapshot()["providers"], [])

    def test_claude_is_visible_only_with_current_quota(self):
        import time
        windows = {"5h": {"remaining": 52.0, "reset": time.time() + 300}, "week": None}
        with patch.object(cotacli, "find_cli", side_effect=lambda name: "/bin/true" if name == "claude" else None), \
             patch.object(cotacli, "get_claude", return_value=(windows, "")):
            self.assertEqual([item["id"] for item in cotacli.snapshot()["providers"]], ["claude"])
        self.assertFalse(cotacli.has_current_quota({"5h": {"remaining": 52.0, "reset": time.time() - 1}}))

    def test_saved_agi_executable_works_without_terminal_path(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "cli-paths.json"
            config.write_text(json.dumps({"agy": "/bin/true"}), encoding="utf-8")
            with patch.object(cotacli, "CLI_PATHS", config), patch.object(cotacli.shutil, "which", return_value=None):
                self.assertEqual(cotacli.find_cli("agy"), "/bin/true")

    def test_snapshot_command_writes_one_json_document(self):
        with patch.object(cotacli, "find_cli", return_value=None):
            with patch.object(sys, "argv", ["cotacli", "snapshot"]):
                from io import StringIO
                with patch.object(sys, "stdout", new_callable=StringIO) as stream:
                    self.assertEqual(cotacli.main(), 0)
                    self.assertEqual(json.loads(stream.getvalue())["providers"], [])

    def test_agy_rejects_usage_that_consumed_tokens(self):
        output = {"status": "SUCCESS", "command": {"name": "usage", "data": {"groups": []}},
                  "usage": {"total_tokens": 1}, "num_turns": 0}
        completed = subprocess.CompletedProcess([], 0, json.dumps(output), "")
        with patch.object(cotacli, "find_cli", return_value="/bin/true"), \
             patch.object(cotacli.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "turno ou tokens"):
                cotacli.read_agy_cli()

    def test_agy_discovered_in_terminal_remains_visible_from_plasma_path(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            bin_dir = base / "bin"
            bin_dir.mkdir()
            fixture = {
                "status": "SUCCESS", "num_turns": 0, "usage": {"total_tokens": 0},
                "command": {"name": "usage", "data": {"groups": [{"buckets": [
                    {"id": "gemini-5h", "remaining_fraction": 1.0},
                    {"id": "gemini-weekly", "remaining_fraction": 0.91},
                    {"id": "3p-5h", "remaining_fraction": 1.0},
                    {"id": "3p-weekly", "remaining_fraction": 1.0},
                ]}]}}
            }
            fake_agy = bin_dir / "agy"
            fake_agy.write_text("#!/bin/sh\nprintf '%s\\n' '" + json.dumps(fixture) + "'\n", encoding="utf-8")
            fake_agy.chmod(0o755)
            script = str(Path(cotacli.__file__).resolve())
            env = os.environ.copy()
            env.update({"HOME": directory, "XDG_CONFIG_HOME": str(base / "config"),
                        "XDG_CACHE_HOME": str(base / "cache"),
                        "PATH": str(bin_dir) + ":/usr/bin:/bin"})
            subprocess.run([sys.executable, script, "discover"], env=env, check=True,
                           capture_output=True, text=True)
            env["PATH"] = "/usr/bin:/bin"
            result = subprocess.run([sys.executable, script, "snapshot", "--refresh"],
                                    env=env, check=True, capture_output=True, text=True)
            providers = json.loads(result.stdout)["providers"]
            self.assertEqual([provider["id"] for provider in providers],
                             ["agy-gemini", "agy-others"])
            self.assertEqual(providers[0]["windows"]["week"]["remaining"], 91.0)


if __name__ == "__main__":
    unittest.main()

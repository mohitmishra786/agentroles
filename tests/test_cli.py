from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from agentroles.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCLIValidate:
    def test_validate_valid_full(self):
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "-c", str(FIXTURES_DIR / "valid_full.yaml")])
        assert result.exit_code == 0
        assert "PASSED" in result.output

    def test_validate_valid_minimal(self):
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "-c", str(FIXTURES_DIR / "valid_minimal.yaml")])
        assert result.exit_code == 0
        assert "PASSED" in result.output

    def test_validate_invalid_missing_roles(self):
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "-c", str(FIXTURES_DIR / "invalid_missing_roles.yaml")])
        assert result.exit_code == 1
        assert "FAILED" in result.output

    def test_validate_claude_non_anthropic_shows_warning(self):
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "-c", str(FIXTURES_DIR / "invalid_claude_non_anthropic.yaml")])
        assert result.exit_code == 0
        assert "WARN" in result.output or "warning" in result.output.lower()

    def test_validate_extra_aider_role_shows_warning(self):
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "-c", str(FIXTURES_DIR / "invalid_extra_aider_role.yaml")])
        assert result.exit_code == 0
        assert "WARN" in result.output or "warning" in result.output.lower()


class TestCLIBuild:
    def test_build_generates_files(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config_path = tmp / "agentroles.yaml"
            config_path.write_text((FIXTURES_DIR / "valid_full.yaml").read_text())

            result = runner.invoke(main, ["build", "-c", str(config_path)])
            assert result.exit_code == 0
            assert "Generated" in result.output

            assert (tmp / "opencode.json").exists()
            assert (tmp / ".claude" / "agents" / "planner.md").exists()
            assert (tmp / ".aider.conf.yml").exists()
            assert (tmp / "litellm-config.yaml").exists()

    def test_build_no_targets(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config_path = tmp / "agentroles.yaml"
            config_path.write_text((FIXTURES_DIR / "valid_minimal.yaml").read_text())

            result = runner.invoke(main, ["build", "-c", str(config_path)])
            assert result.exit_code == 0


class TestCLIMigrate:
    def test_migrate_prints_message(self):
        runner = CliRunner()
        result = runner.invoke(main, ["migrate"])
        assert result.exit_code == 0
        assert "No migrations needed" in result.output
        assert "schema version 1" in result.output


class TestCLIInit:
    def test_init_creates_config(self):
        import os

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = runner.invoke(
                    main,
                    ["init", "-t", "opencode", "-t", "litellm_proxy", "-y"],
                )
                assert result.exit_code == 0

                wd = Path(tmpdir)
                assert (wd / "agentroles.yaml").exists()
                assert (wd / "opencode.json").exists()
                assert (wd / "litellm-config.yaml").exists()
            finally:
                os.chdir(original_cwd)

    def test_init_without_targets(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                main,
                ["init", "-y", "--targets", "opencode"],
            )
            assert result.exit_code == 0


class TestCLIHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "build" in result.output
        assert "validate" in result.output
        assert "migrate" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "agentroles" in result.output

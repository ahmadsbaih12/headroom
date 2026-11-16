"""``--code-memory graphify`` registers the Graphify MCP server per project."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from headroom.cli import wrap as wrap_cli
from headroom.mcp_registry import build_graphify_spec
from headroom.mcp_registry.claude import SCOPE_LOCAL, ClaudeRegistrar


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HEADROOM_WORKSPACE_DIR", str(tmp_path / ".headroom"))
    monkeypatch.delenv("HEADROOM_CODE_MEMORY", raising=False)
    real_which = shutil.which
    monkeypatch.setattr(
        wrap_cli.shutil,
        "which",
        lambda name, *a, **k: "/usr/bin/uvx" if name == "uvx" else real_which(name, *a, **k),
    )


def _registrar(tmp_path: Path) -> ClaudeRegistrar:
    (tmp_path / ".claude").mkdir(exist_ok=True)
    return ClaudeRegistrar(
        claude_cli=None, home_dir=tmp_path, scope=SCOPE_LOCAL, project_dir=tmp_path / "proj"
    )


def _project_servers(tmp_path: Path) -> dict[str, Any]:
    config = json.loads((tmp_path / ".claude.json").read_text(encoding="utf-8"))
    return config["projects"][(tmp_path / "proj").as_posix()]["mcpServers"]


def test_spec_runs_graphify_mcp_over_stdio() -> None:
    spec = build_graphify_spec()
    assert spec.name == "graphify"
    assert spec.command == "uvx"
    assert "graphify-mcp" in spec.args


def test_graphify_selection_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HEADROOM_CODE_MEMORY", "graphify")
    assert wrap_cli._resolve_code_memory({}) == "graphify"


def test_setup_registers_for_this_project_and_hints_at_missing_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    wrap_cli._setup_graphify_mcp(_registrar(tmp_path), verbose=True)

    assert "graphify" in _project_servers(tmp_path)
    assert "/graphify ." in capsys.readouterr().out


def test_none_selection_removes_only_headroom_installed_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    registrar = _registrar(tmp_path)
    wrap_cli._setup_graphify_mcp(registrar)
    assert "graphify" in _project_servers(tmp_path)

    wrap_cli._disable_graphify_mcp(registrar)
    assert "graphify" not in _project_servers(tmp_path)


def test_user_managed_entry_is_left_alone(tmp_path: Path) -> None:
    registrar = _registrar(tmp_path)
    from headroom.mcp_registry.base import ServerSpec

    registrar.register_server(ServerSpec(name="graphify", command="my-graphify"))
    wrap_cli._disable_graphify_mcp(registrar)
    assert "graphify" in _project_servers(tmp_path)

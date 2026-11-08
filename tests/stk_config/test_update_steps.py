import os
from pathlib import Path

import pytest

from stk.engine.registry import discover_components
from stk.engine.update_step import StepOutcome
from stk.setup import Setup
from stk.testing import RecordingContext
from stk.updates.registry import all_update_steps
from stk_config.components.mise.mise import update_mise


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))


def all_step_names() -> list[str]:
    components = discover_components("stk_config.components")
    setup = Setup(components=components, checkout=Path("/checkout"))
    return [step.name for step in all_update_steps(setup, components)]


def test_step_names_are_unique() -> None:
    names = all_step_names()

    assert len(names) == len(set(names))


def test_mise_is_updated_before_the_components_using_it() -> None:
    names = all_step_names()

    assert names.index("mise") < names.index("tmux")
    assert names.index("mise") < names.index("neovim")


def test_mise_is_updated_with_prebuilt_binaries() -> None:
    context = RecordingContext()

    assert update_mise(context) is StepOutcome.UPDATED

    assert [command[1:] for command in context.commands] == [
        ["self-update", "--yes"],
        ["upgrade", "--yes"],
        ["prune", "--yes"],
    ]
    assert all(
        env == {"MISE_NODE_COMPILE": "false", "MISE_PYTHON_COMPILE": "false"}
        for env in context.environments[:2]
    )


def test_mise_bump_rewrites_and_commits_the_pinned_versions() -> None:
    context = RecordingContext()
    context.bump_versions = True

    update_mise(context)

    assert context.commands[1][1:] == ["upgrade", "--yes", "--bump"]
    assert ["git", "add", "*/files/mise.toml"] in context.commands
    assert ["git", "commit", "-m", "Version bump"] in context.commands


def test_environment_is_not_modified() -> None:
    before = dict(os.environ)

    update_mise(RecordingContext())

    assert dict(os.environ) == before

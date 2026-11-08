from pathlib import Path

from stk.engine.component import Component
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.helpers.commands import run_command
from stk.helpers.links import symlink_file
from stk.helpers.mise import (
    MISE_INSTALL_SCRIPT_URL,
    MISE_IS_INSTALLED,
    mise_config_directory,
    mise_executable,
)
from stk.updates.version_bump import commit_and_offer_push

FILES = Path(__file__).resolve().parent / "files"
# The configs in conf.d link here, so bumping rewrites the pinned versions in place
COMPONENTS_DIRECTORY = Path(__file__).parents[1]
COMPONENT_MISE_CONFIGS = "*/files/mise.toml"


def apply_mise() -> None:
    if not mise_executable().exists():
        # Downloading first, as a failing curl in a pipe would run an empty script
        run_command(
            "Install mise",
            'installer="$(mktemp)"'
            + " && trap 'rm -f \"$installer\"' EXIT"
            + f' && curl -fsSL {MISE_INSTALL_SCRIPT_URL} -o "$installer"'
            + ' && sh "$installer"',
        )
    symlink_file(FILES / "mise.toml", mise_config_directory() / "mise.toml")


def update_mise(context: UpdateContext) -> StepOutcome:
    context.section("Updating Mise Packages 📦")
    mise = str(mise_executable())
    context.run([mise, "self-update", "--yes"])
    upgrade = [mise, "upgrade", "--yes", *(["--bump"] if context.bump_versions else [])]
    # From home, so that a project config in the current directory is left alone
    context.run(upgrade, working_directory=Path.home())
    if context.bump_versions:
        commit_and_offer_push(context, COMPONENTS_DIRECTORY, COMPONENT_MISE_CONFIGS)
    # Pins moved by a pull leave their previous versions installed
    context.run([mise, "prune", "--yes"])
    return StepOutcome.UPDATED


MISE_UPDATE = UpdateStep("mise", update_mise, requires=(MISE_IS_INSTALLED,))


MISE = Component("mise", apply_mise, update=MISE_UPDATE)

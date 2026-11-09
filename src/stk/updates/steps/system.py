from collections.abc import Callable
from dataclasses import dataclass

from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.machine import has_executable
from stk.setup import Setup
from stk.updates.version_bump import commit_and_offer_push

NIX_GENERATIONS_TO_KEEP = "7d"


@dataclass(frozen=True)
class SystemUpdater:
    requirement: Requirement
    update: Callable[[UpdateContext, Setup], None]


def update_with_apt(context: UpdateContext, _setup: Setup) -> None:
    context.run(["sudo", "apt", "update"])
    context.run(["sudo", "apt", "upgrade", "--yes"])


def update_nixos(context: UpdateContext, setup: Setup) -> None:
    flake = setup.nixos_flake
    if flake is None:
        context.run(["sudo", "nixos-rebuild", "switch"])
    else:
        if context.bump_versions:
            context.run(["nix", "flake", "update"], working_directory=flake)
            commit_and_offer_push(context, flake, "flake.lock")
        context.run(["sudo", "nixos-rebuild", "switch", "--flake", str(flake)])
    context.run(
        ["sudo", "nix-collect-garbage", "--delete-older-than", NIX_GENERATIONS_TO_KEEP]
    )
    context.run(["nix", "store", "gc"])


SYSTEM_UPDATERS = (
    SystemUpdater(has_executable("apt"), update_with_apt),
    SystemUpdater(has_executable("nixos-rebuild"), update_nixos),
)


def applicable_system_updater() -> SystemUpdater | None:
    return next(
        (updater for updater in SYSTEM_UPDATERS if updater.requirement.is_met()), None
    )


def update_system(context: UpdateContext, setup: Setup) -> StepOutcome:
    updater = applicable_system_updater()
    if updater is None:
        return StepOutcome.SKIPPED
    context.section("Updating System Packages 📦")
    updater.update(context, setup)
    return StepOutcome.UPDATED


def system_update_step(setup: Setup) -> UpdateStep:
    supported_system = Requirement(
        "a supported system package manager",
        lambda: applicable_system_updater() is not None,
    )
    return UpdateStep(
        "system",
        lambda context: update_system(context, setup),
        requires=(supported_system,),
        uses_sudo=True,
    )

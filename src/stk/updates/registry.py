from dataclasses import replace

from stk.engine.component import Component
from stk.engine.update_step import UpdateStep
from stk.setup import Setup
from stk.updates.steps.stk import stk_update_step
from stk.updates.steps.system import system_update_step


def core_update_steps(setup: Setup) -> tuple[UpdateStep, ...]:
    # Not owned by a component, and the first to run:
    # a newer configuration and fresh system packages are what the component steps
    # build on
    return (system_update_step(setup), stk_update_step(setup))


def component_update_steps(
    components: tuple[Component, ...],
) -> tuple[UpdateStep, ...]:
    # A component's step only makes sense where the component itself applies
    return tuple(
        replace(
            component.update, requires=(*component.requires, *component.update.requires)
        )
        for component in components
        if component.update is not None
    )


def all_update_steps(
    setup: Setup, components: tuple[Component, ...]
) -> tuple[UpdateStep, ...]:
    return (*core_update_steps(setup), *component_update_steps(components))

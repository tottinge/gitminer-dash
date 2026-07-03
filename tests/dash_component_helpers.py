"""Shared Dash component traversal helpers for test assertions."""

from __future__ import annotations


def walk_components(component):
    if component is None:
        return
    yield component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from walk_components(child)
        return
    if children is None or isinstance(children, str):
        return
    yield from walk_components(children)


def find_component_by_id(component, component_id: str):
    for item in walk_components(component):
        if getattr(item, "id", None) == component_id:
            return item
    msg = f"Component not found for id={component_id}"
    raise AssertionError(msg)


def component_ids(component) -> set[str]:
    return {
        comp_id
        for comp_id in (
            getattr(item, "id", None) for item in walk_components(component)
        )
        if comp_id
    }

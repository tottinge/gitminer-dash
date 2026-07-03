"""Layout/style tests for AI Insights usability improvements."""

from tests import setup_path
from tests.dash_component_helpers import (
    component_ids as _ids_under,
)
from tests.dash_component_helpers import (
    find_component_by_id as _find_by_id,
)
from tests.dash_component_helpers import (
    walk_components as _walk_components,
)

setup_path()
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@patch("dash.register_page")
def test_main_table_styles_include_theme_scroll_and_trend_cues(_):
    import pages.ai_insights as module

    table = _find_by_id(module.layout, "id-ai-insights-table")

    assert table.style_table == module.MAIN_TABLE_STYLE_TABLE
    assert table.style_header == module.MAIN_TABLE_HEADER_STYLE
    assert table.fixed_rows == {"headers": True}
    assert (
        table.style_data_conditional == module.MAIN_TABLE_STYLE_DATA_CONDITIONAL
    )

    trend_backgrounds = {
        rule["if"]["filter_query"]: rule["backgroundColor"]
        for rule in table.style_data_conditional
        if rule.get("if", {}).get("filter_query")
    }
    assert trend_backgrounds['{trend} = "rising"'] == "#fff7e6"
    assert trend_backgrounds['{trend} = "falling"'] == "#e6f7f1"
    assert trend_backgrounds['{trend} = "new"'] == "#f3e8ff"

    selected_rules = [
        rule
        for rule in table.style_data_conditional
        if rule.get("if", {}).get("state") == "selected"
    ]
    assert len(selected_rules) == 1
    assert selected_rules[0]["backgroundColor"] == "#dbeafe"


@patch("dash.register_page")
def test_drilldown_tables_use_two_panes_and_shared_theme(_):
    import pages.ai_insights as module

    details_table = _find_by_id(
        module.layout, "id-ai-insights-drilldown-details"
    )
    evidence_table = _find_by_id(
        module.layout, "id-ai-insights-drilldown-evidence"
    )

    assert details_table.style_table == module.DRILLDOWN_TABLE_STYLE_TABLE
    assert evidence_table.style_table == module.DRILLDOWN_TABLE_STYLE_TABLE
    assert details_table.style_header == module.DRILLDOWN_TABLE_HEADER_STYLE
    assert evidence_table.style_header == module.DRILLDOWN_TABLE_HEADER_STYLE
    assert details_table.fixed_rows == {"headers": True}
    assert evidence_table.fixed_rows == {"headers": True}
    assert (
        details_table.style_data_conditional
        == module.TABLE_ZEBRA_STYLE_CONDITIONAL
    )
    assert (
        evidence_table.style_data_conditional
        == module.TABLE_ZEBRA_STYLE_CONDITIONAL
    )

    required_ids = {
        "id-ai-insights-drilldown-details",
        "id-ai-insights-drilldown-evidence",
    }
    two_pane_containers = [
        component
        for component in _walk_components(module.layout)
        if getattr(component, "style", None)
        == {"display": "flex", "gap": "12px", "flexWrap": "wrap"}
    ]
    assert any(
        required_ids.issubset(_ids_under(component))
        for component in two_pane_containers
    )


@patch("dash.register_page")
def test_narrative_section_copy_and_invalid_claims_table_style(_):
    import pages.ai_insights as module

    narrative_pre = _find_by_id(module.layout, "id-ai-insights-narrative-text")
    invalid_claims_table = _find_by_id(
        module.layout, "id-ai-insights-narrative-invalid-claims"
    )

    assert narrative_pre.style == module.NARRATIVE_PRE_STYLE
    assert (
        invalid_claims_table.style_table
        == module.INVALID_CLAIMS_TABLE_STYLE_TABLE
    )
    assert (
        invalid_claims_table.style_header
        == module.INVALID_CLAIMS_TABLE_HEADER_STYLE
    )
    assert invalid_claims_table.fixed_rows == {"headers": True}
    assert (
        invalid_claims_table.style_data_conditional
        == module.TABLE_ZEBRA_STYLE_CONDITIONAL
    )

    text_children = {
        item.children
        for item in _walk_components(module.layout)
        if isinstance(getattr(item, "children", None), str)
    }
    assert module.DRILLDOWN_HELPER_TEXT in text_children
    assert module.NARRATIVE_HELPER_TEXT in text_children

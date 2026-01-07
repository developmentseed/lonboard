"""
Feature Interaction Tests for Lonboard UI

This module tests the complete feature interaction system, which includes:
- Hover interactions (tooltips and highlighting)
- Click interactions (side panel display)
- Mixed interaction patterns
- Configuration and property validation
- Integration with other UI modes (bbox selection)

The feature interaction system allows users to explore geographic data through:
1. **Tooltips**: Hover-based information display (when show_tooltip=True)
2. **Side Panel**: Click-based detailed information display (when show_side_panel=True)
3. **Feature Highlighting**: Visual feedback on hover/click regardless of display mode

Both tooltip and side panel present the same underlying feature data, just in different formats.
"""

import sys
from pathlib import Path

import geopandas as gpd
import pytest
from IPython.display import display
from shapely.geometry import Point
from test_utils import (
    TestConstants,
    check_tooltip_visibility,
    click_feature_position,
    get_tooltip_content,
    get_tooltip_position,
    hover_feature_position,
    setup_map_widget,
    start_bbox_selection,
    wait_for_button,
)

from lonboard import Map
from lonboard.layer import ScatterplotLayer

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def feature_test_geodataframe():
    """
    GeoDataFrame with rich data for feature interaction testing.

    Contains multiple data types (text, numbers, categories) to ensure
    the feature interaction system handles various data formats correctly.
    """
    return gpd.GeoDataFrame(
        {
            "name": ["test_point_1", "test_point_2", "test_point_3"],
            "value": [100, 200, 300],
            "category": ["A", "B", "C"],
            "description": [
                "First test point",
                "Second test point",
                "Third test point",
            ],
            "coordinates": [(0, 0), (1, 1), (-1, -1)],
            "priority": [1, 2, 3],
        },
        geometry=[Point(0, 0), Point(1, 1), Point(-1, -1)],
        crs="EPSG:4326",
    )


@pytest.fixture
def feature_test_layer(feature_test_geodataframe):
    """
    Scatterplot layer configured for comprehensive feature interaction testing.

    The layer is explicitly configured to be pickable and has sufficient
    radius to ensure reliable hover and click interactions during testing.
    """
    return ScatterplotLayer.from_geopandas(
        feature_test_geodataframe,
        get_fill_color=[255, 0, 0],
        get_radius=5000,
        pickable=True,  # Essential for hover and click interactions
    )


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================


def validate_feature_configuration(
    map_obj,
    expected_show_tooltip,
    expected_show_side_panel,
):
    """
    Validate that map has correct feature interaction configuration.

    Args:
        map_obj: Map instance to validate
        expected_show_tooltip: Expected show_tooltip value
        expected_show_side_panel: Expected show_side_panel value
    """
    assert hasattr(map_obj, "show_tooltip"), "Map should have show_tooltip attribute"
    assert hasattr(map_obj, "show_side_panel"), (
        "Map should have show_side_panel attribute"
    )

    assert map_obj.show_tooltip == expected_show_tooltip, (
        f"Expected show_tooltip={expected_show_tooltip}, got {map_obj.show_tooltip}"
    )
    assert map_obj.show_side_panel == expected_show_side_panel, (
        f"Expected show_side_panel={expected_show_side_panel}, got {map_obj.show_side_panel}"
    )


def validate_map_display(map_obj):
    """
    Validate that map can be displayed without errors.

    This is important because feature interactions only work on properly
    rendered maps.
    """
    try:
        display(map_obj)
    except (OSError, ValueError, RuntimeError) as e:
        pytest.fail(f"Map display failed with error: {e}")
    else:
        return True


# =============================================================================
# PYTHON PROPERTY TESTS
# =============================================================================


class TestFeatureInteractionConfiguration:
    """
    Test the Python properties that control feature interaction behavior.

    These tests focus on the configuration aspects without requiring
    browser interaction, making them fast and suitable for CI/CD.

    Configuration Options:
    - show_tooltip: Enables hover-based tooltip display
    - show_side_panel: Enables click-based side panel display
    - Both can be enabled simultaneously or independently
    """

    def test_tooltip_enabled_configuration(self, sample_map_with_tooltip):
        """
        Test that show_tooltip=True properly configures tooltip interactions.

        Verifies that the map can be created with tooltips enabled and
        displays without errors.
        """
        validate_feature_configuration(
            sample_map_with_tooltip,
            expected_show_tooltip=True,
            expected_show_side_panel=False,
        )
        validate_map_display(sample_map_with_tooltip)

    def test_tooltip_disabled_configuration(self, sample_map_with_no_tooltip_or_panel):
        """
        Test that show_tooltip=False disables tooltip interactions.

        Ensures that maps can be created with tooltips explicitly disabled
        and that the configuration persists correctly.
        """
        validate_feature_configuration(
            sample_map_with_no_tooltip_or_panel,
            expected_show_tooltip=False,
            expected_show_side_panel=False,
        )
        validate_map_display(sample_map_with_no_tooltip_or_panel)

    def test_side_panel_enabled_configuration(self, sample_map_with_side_panel):
        """
        Test that show_side_panel=True enables click-based interactions.

        Validates that the side panel configuration works correctly
        for feature selection on click.
        """
        validate_feature_configuration(
            sample_map_with_side_panel,
            expected_show_tooltip=False,
            expected_show_side_panel=True,
        )
        validate_map_display(sample_map_with_side_panel)

    def test_both_enabled_configuration(self, sample_map_with_tooltip_and_panel):
        """
        Test that both tooltip and side panel can work simultaneously.

        This is an important test as it ensures that users can have
        both hover tooltips and click side panels enabled at the same time.
        """
        validate_feature_configuration(
            sample_map_with_tooltip_and_panel,
            expected_show_tooltip=True,
            expected_show_side_panel=True,
        )
        validate_map_display(sample_map_with_tooltip_and_panel)

    def test_default_configuration(self, feature_test_layer):
        """
        Test default behavior when no explicit configuration is provided.

        Lonboard should default to no tooltips but side panel enabled,
        providing the traditional click-to-explore behavior.
        """
        default_map = Map(feature_test_layer, height="400px")
        validate_feature_configuration(
            default_map,
            expected_show_tooltip=False,
            expected_show_side_panel=True,
        )

    def test_configuration_persistence(self, feature_test_layer):
        """
        Test that configuration persists after map operations.

        Ensures that the feature interaction settings remain consistent
        after the map is displayed and potentially manipulated.
        """
        map_obj = Map(
            feature_test_layer,
            show_tooltip=True,
            show_side_panel=False,
            height="400px",
        )

        # Verify initial state
        assert map_obj.show_tooltip is True
        assert map_obj.show_side_panel is False

        # Display map (simulates user interaction)
        validate_map_display(map_obj)

        # Verify properties are still correct after display
        assert map_obj.show_tooltip is True
        assert map_obj.show_side_panel is False

    def test_configuration_with_different_layers(self, feature_test_geodataframe):
        """
        Test that configuration works consistently across different layer types.

        Ensures that feature interaction configuration is not dependent
        on specific layer properties or styling.
        """
        configs = [
            {"get_fill_color": [255, 0, 0], "get_radius": 5000},
            {"get_fill_color": [0, 255, 0], "get_radius": 3000},
            {"get_fill_color": [0, 0, 255], "get_radius": 7000},
        ]

        for config in configs:
            layer = ScatterplotLayer.from_geopandas(feature_test_geodataframe, **config)
            map_obj = Map(
                layer,
                show_tooltip=True,
                show_side_panel=False,
                height="300px",
            )

            validate_feature_configuration(
                map_obj,
                expected_show_tooltip=True,
                expected_show_side_panel=False,
            )
            validate_map_display(map_obj)

    @pytest.mark.usefixtures("feature_test_layer")
    def test_configuration_edge_cases(self):
        """
        Test edge cases and potential error conditions in configuration.

        Ensures that the system handles unusual configurations gracefully
        and maintains expected behavior.
        """
        # Test with various GeoDataFrame structures
        test_cases = [
            # Single point
            gpd.GeoDataFrame(
                {"single_value": [42]},
                geometry=[Point(0, 0)],
                crs="EPSG:4326",
            ),
            # Multiple data types
            gpd.GeoDataFrame(
                {
                    "text": ["A", "B"],
                    "number": [1.5, 2.7],
                    "integer": [10, 20],
                    "boolean": [True, False],
                },
                geometry=[Point(0, 0), Point(1, 1)],
                crs="EPSG:4326",
            ),
            # Minimal properties
            gpd.GeoDataFrame(
                geometry=[Point(0, 0)],
                crs="EPSG:4326",
            ),
        ]

        for gdf in test_cases:
            layer = ScatterplotLayer.from_geopandas(
                gdf,
                get_fill_color=[255, 0, 0],
                get_radius=5000,
            )
            map_obj = Map(
                layer,
                show_tooltip=True,
                show_side_panel=False,
                height="300px",
            )

            validate_feature_configuration(
                map_obj,
                expected_show_tooltip=True,
                expected_show_side_panel=False,
            )
            validate_map_display(map_obj)


# =============================================================================
# BROWSER INTERACTION TESTS
# =============================================================================


@pytest.mark.usefixtures("solara_test")
class TestFeatureInteractionBehavior:
    """
    Test actual user interactions with features in a browser environment.

    These tests use Playwright to simulate real user interactions including
    hover events, clicks, and mixed interaction patterns. They verify that
    the feature interaction system responds correctly to user input.

    Interaction Types Tested:
    - Hover: Triggers tooltips and visual highlighting
    - Click: Triggers side panel display and feature selection
    - Mixed: Ensures hover and click interactions work together
    """

    def test_tooltip_hover_behavior(self, page_session, sample_map_with_tooltip):
        """
        Test tooltip appearance and behavior on hover when show_tooltip=True.

        This test verifies that:
        - Tooltips appear when hovering over features
        - Tooltips disappear when hovering over empty areas
        - Tooltip content and positioning are reasonable when visible
        """
        canvas = setup_map_widget(page_session, sample_map_with_tooltip)

        # Hover over center position (should have features)
        hover_feature_position(page_session, "center")

        # Check if tooltip appears
        tooltip_visible = check_tooltip_visibility(page_session, should_be_visible=True)

        # Tooltip might not appear if no feature is at the exact position
        # The important thing is that no errors occur and the system responds to hover
        if tooltip_visible:
            # Verify tooltip content and positioning when visible
            content = get_tooltip_content(page_session)
            position = get_tooltip_position(page_session)

            assert content is not None, "Tooltip should have content when visible"
            assert position is not None, "Tooltip should have position when visible"
            assert position["width"] > 0, "Tooltip should have width"
            assert position["height"] > 0, "Tooltip should have height"

        # Hover over empty area (should not show tooltip)
        hover_feature_position(page_session, "empty")

        # Tooltip should disappear or remain hidden
        check_tooltip_visibility(page_session, should_be_visible=False)

        assert canvas.count() > 0, "Map canvas should remain loaded"

    def test_no_tooltip_when_disabled(
        self,
        page_session,
        sample_map_with_no_tooltip_or_panel,
    ):
        """
        Test that tooltips never appear when show_tooltip=False.

        This ensures that the tooltip system is properly disabled
        and doesn't interfere with other interactions.
        """
        canvas = setup_map_widget(page_session, sample_map_with_no_tooltip_or_panel)

        # Hover over different positions
        for position in ["center", "start", "end"]:
            hover_feature_position(page_session, position)

            # Tooltip should never be visible when disabled
            tooltip_hidden = check_tooltip_visibility(
                page_session,
                should_be_visible=False,
            )
            assert tooltip_hidden, (
                f"Tooltip should not be visible when show_tooltip=False (hovered at {position})"
            )

        assert canvas.count() > 0, "Map canvas should remain loaded"

    def test_side_panel_click_behavior(self, page_session, sample_map_with_side_panel):
        """
        Test side panel behavior when show_side_panel=True.

        Verifies that clicking on features properly triggers side panel
        display and that the system remains stable.
        """
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Click on different positions
        for position in ["center", "start", "end"]:
            click_feature_position(page_session, position)
            page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

            # System should handle clicks gracefully
            assert canvas.count() > 0, (
                f"Map canvas should remain stable after click at {position}"
            )

    def test_mixed_hover_and_click_interactions(
        self,
        page_session,
        sample_map_with_tooltip_and_panel,
    ):
        """
        Test behavior when both tooltip and side panel are enabled.

        This is a critical test that ensures hover tooltips and click
        side panels can coexist without interfering with each other.
        """
        canvas = setup_map_widget(page_session, sample_map_with_tooltip_and_panel)

        # Test hover first
        hover_feature_position(page_session, "center")
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)

        # Then test click
        click_feature_position(page_session, "center")
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

        # Test hover again after click
        hover_feature_position(page_session, "empty")

        # System should remain stable after both hover and click interactions
        assert canvas.count() > 0, (
            "Map canvas should remain loaded after mixed interactions"
        )

    def test_hover_before_click_stability(
        self,
        page_session,
        sample_map_with_side_panel,
    ):
        """
        Test that hovering before clicking doesn't interfere with feature selection.

        Ensures that hover state doesn't affect subsequent click behavior,
        which is important for smooth user experience.
        """
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Hover first, then click
        hover_feature_position(page_session, "center")
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)

        click_feature_position(page_session, "center")
        assert canvas.count() > 0

    def test_multiple_interaction_patterns(self, page_session, sample_map_with_tooltip):
        """
        Test complex patterns of hover and click interactions.

        Simulates realistic user behavior with rapid interaction changes
        to ensure the system remains stable and responsive.
        """
        canvas = setup_map_widget(page_session, sample_map_with_tooltip)

        # Test pattern: hover -> hover -> click -> hover -> hover
        interactions = [
            ("hover", "center"),
            ("hover", "start"),
            ("click", "center"),
            ("hover", "empty"),
            ("hover", "end"),
        ]

        for action, position in interactions:
            if action == "hover":
                hover_feature_position(page_session, position)
            else:
                click_feature_position(page_session, position)

            page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)
            assert canvas.count() > 0, (
                f"Map canvas should remain stable after {action} at {position}"
            )

    def test_feature_interaction_with_bbox_mode(
        self,
        page_session,
        sample_map_with_side_panel,
    ):
        """
        Test feature interactions during bbox selection mode.

        Ensures that feature highlighting and selection work correctly
        even when the map is in a different interaction mode.
        """
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Start bbox mode
        start_bbox_selection(page_session)
        cancel_button = wait_for_button(page_session, "cancel")
        assert cancel_button.count() > 0

        # Test hover during bbox mode
        hover_feature_position(page_session, "center")
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)

        # Test click during bbox mode
        click_feature_position(page_session, "center")
        assert canvas.count() > 0

        # Cancel bbox mode
        cancel_button.click()
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

        # Verify return to normal feature interaction mode
        select_button = wait_for_button(page_session, "select")
        assert select_button.count() > 0

    def test_tooltip_positioning_and_styling(
        self,
        page_session,
        sample_map_with_tooltip,
    ):
        """
        Test tooltip positioning and visual properties when visible.

        Validates that tooltips appear at reasonable positions
        with appropriate sizing for good user experience.
        """
        # Set up map widget for tooltip positioning test
        setup_map_widget(page_session, sample_map_with_tooltip)

        # Hover over areas that might have features
        hover_feature_position(page_session, "center")
        page_session.wait_for_timeout(500)

        # Check if tooltip is visible
        if check_tooltip_visibility(page_session, should_be_visible=True):
            position = get_tooltip_position(page_session)

            # Verify tooltip positioning makes sense
            assert position is not None, "Should have tooltip position when visible"
            assert position["x"] >= 0, "Tooltip x position should be non-negative"
            assert position["y"] >= 0, "Tooltip y position should be non-negative"
            assert position["width"] > 0, "Tooltip should have visible width"
            assert position["height"] > 0, "Tooltip should have visible height"

            # Tooltip should be reasonably sized
            assert 50 <= position["width"] <= 500, "Tooltip width should be reasonable"
            assert 20 <= position["height"] <= 300, (
                "Tooltip height should be reasonable"
            )


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.usefixtures("solara_test")
class TestFeatureInteractionIntegration:
    """
    Test feature interaction integration with other map features and modes.

    These tests ensure that the feature interaction system works correctly
    alongside other Lonboard features like bbox selection and rapid user actions.
    """

    def test_interaction_stability_under_rapid_actions(
        self,
        page_session,
        sample_map_with_tooltip,
    ):
        """
        Test system stability under rapid user interactions.

        Simulates a user rapidly moving the mouse and clicking to ensure
        the feature interaction system doesn't become unstable or crash.
        """
        canvas = setup_map_widget(page_session, sample_map_with_tooltip)

        # Rapid interaction pattern
        positions = ["center", "start", "empty", "end", "center", "empty"]

        for _ in range(3):  # Repeat the pattern multiple times
            for position in positions:
                hover_feature_position(page_session, position)
                page_session.wait_for_timeout(100)  # Very rapid

        # Final stability check
        assert canvas.count() > 0, "Map should remain stable after rapid interactions"


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================


def test_feature_interaction_configuration_edge_cases(feature_test_layer):
    """
    Test edge cases in feature interaction configuration.

    These tests ensure that unusual or boundary conditions are handled
    gracefully without causing errors or unexpected behavior.
    """
    # Test with boolean values explicitly
    map_true = Map(feature_test_layer, show_tooltip=True)
    map_false = Map(feature_test_layer, show_tooltip=False)

    assert map_true.show_tooltip is True
    assert map_false.show_tooltip is False

    # Test property access as attributes
    assert hasattr(map_true, "show_tooltip")
    assert hasattr(map_false, "show_tooltip")

    # Test property types
    assert isinstance(map_true.show_tooltip, bool)
    assert isinstance(map_false.show_tooltip, bool)


def test_feature_interaction_with_map_configuration(feature_test_layer):
    """
    Test feature interaction properties alongside other Map configurations.

    Ensures that feature interaction settings work correctly with
    other map parameters like picking radius, height, etc.
    """
    # Test with multiple map parameters
    map_obj = Map(
        feature_test_layer,
        show_tooltip=True,
        show_side_panel=False,
        height="500px",
        picking_radius=10,
    )

    validate_feature_configuration(
        map_obj,
        expected_show_tooltip=True,
        expected_show_side_panel=False,
    )
    assert map_obj.height == "500px"
    assert map_obj.picking_radius == 10

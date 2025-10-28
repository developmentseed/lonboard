"""Test mesh generation for SurfaceLayer."""

import numpy as np

from lonboard.experimental._surface import generate_mesh_grid


def test_generate_mesh_grid_basic():
    """Test basic mesh generation with small grid."""
    n_rows, n_cols = 2, 2
    positions, triangles = generate_mesh_grid(n_rows=n_rows, n_cols=n_cols)

    # Check positions shape: (n_rows+1) * (n_cols+1) vertices
    expected_num_vertices = (n_rows + 1) * (n_cols + 1)  # 3 * 3 = 9
    assert positions.shape == (expected_num_vertices, 2)

    # Check triangles shape: n_rows * n_cols * 2 triangles
    expected_num_triangles = n_rows * n_cols * 2  # 2 * 2 * 2 = 8
    assert triangles.shape == (expected_num_triangles, 3)

    # Check all triangle indices are valid (within vertex range)
    assert np.all(triangles >= 0)
    assert np.all(triangles < expected_num_vertices)

    # Check positions are in [0, 1] range
    assert np.all(positions >= 0)
    assert np.all(positions <= 1)


def test_generate_mesh_grid_single_cell():
    """Test with a single cell (simplest case)."""
    positions, triangles = generate_mesh_grid(n_rows=1, n_cols=1)

    # Should have 4 vertices
    assert positions.shape == (4, 2)

    # Should have 2 triangles
    assert triangles.shape == (2, 3)

    # Verify exact positions for single cell
    expected_positions = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float32)
    np.testing.assert_allclose(positions, expected_positions)

    # Verify triangle indices
    assert np.all(triangles >= 0)
    assert np.all(triangles < 4)


def test_generate_mesh_grid_larger():
    """Test with larger grid to ensure scaling works."""
    n_rows, n_cols = 50, 50
    positions, triangles = generate_mesh_grid(n_rows=n_rows, n_cols=n_cols)

    expected_num_vertices = (n_rows + 1) * (n_cols + 1)  # 51 * 51 = 2601
    expected_num_triangles = n_rows * n_cols * 2  # 50 * 50 * 2 = 5000

    assert positions.shape == (expected_num_vertices, 2)
    assert triangles.shape == (expected_num_triangles, 3)

    # Most important: all indices must be valid
    assert np.all(triangles >= 0)
    assert np.all(triangles < expected_num_vertices)

    # Check corners are correct
    np.testing.assert_allclose(positions[0], [0, 0])  # bottom-left
    np.testing.assert_allclose(positions[n_cols], [1, 0])  # bottom-right
    np.testing.assert_allclose(positions[n_cols * (n_rows + 1)], [0, 1])  # top-left
    np.testing.assert_allclose(
        positions[(n_rows + 1) * (n_cols + 1) - 1],
        [1, 1],
    )  # top-right


def test_triangle_winding():
    """Test that triangles have consistent winding order."""
    positions, triangles = generate_mesh_grid(n_rows=2, n_cols=2)

    # Check that all triangles have counter-clockwise winding
    for tri in triangles:
        v0, v1, v2 = positions[tri]
        # Compute cross product to check winding
        edge1 = v1 - v0
        edge2 = v2 - v0
        cross = edge1[0] * edge2[1] - edge1[1] * edge2[0]
        # For counter-clockwise winding in screen space, cross product should be positive
        # (though this depends on coordinate system)
        assert cross > 0

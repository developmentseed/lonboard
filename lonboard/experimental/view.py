import traitlets as t

from lonboard._base import BaseWidget
from lonboard.view_state import (
    BaseViewState,
    FirstPersonViewState,
    GlobeViewState,
    MapViewState,
    OrbitViewState,
    OrthographicViewState,
)


class BaseView(BaseWidget):
    """A deck.gl [View][deck-view].

    [deck-view]: https://deck.gl/docs/api-reference/core/view

    The `BaseView` class and its subclasses are used to specify where and how your deck.gl layers should be rendered. Applications typically instantiate at least one `BaseView` subclass.
    """

    _view_state_type: type[BaseViewState] = BaseViewState

    x = t.Union([t.Int(), t.Unicode()], allow_none=True, default_value=None).tag(
        sync=True,
    )
    """The x position of the view.

    A relative (e.g. `'50%'`) or absolute position. Default `0`.
    """

    y = t.Union([t.Int(), t.Unicode()], allow_none=True, default_value=None).tag(
        sync=True,
    )
    """The y position of the view.

    A relative (e.g. `'50%'`) or absolute position. Default `0`.
    """

    width = t.Union([t.Int(), t.Unicode()], allow_none=True, default_value=None).tag(
        sync=True,
    )
    """The width of the view.

    A relative (e.g. `'50%'`) or absolute extent. Default `'100%'`.
    """

    height = t.Union([t.Int(), t.Unicode()], allow_none=True, default_value=None).tag(
        sync=True,
    )
    """The height of the view.

    A relative (e.g. `'50%'`) or absolute extent. Default `'100%'`.
    """


class MapView(BaseView):
    """A deck.gl [MapView][deck-map-view].

    [deck-map-view]: https://deck.gl/docs/api-reference/core/map-view

    The `MapView` creates a camera that looks at a geospatial location on a map from a certain direction. The behavior of `MapView` is generally modeled after that of Mapbox GL JS.

    Most geospatial applications will use this view with the default parameters.
    """

    _view_type = t.Unicode("map-view").tag(sync=True)

    _view_state_type = MapViewState

    repeat = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """
    Whether to render multiple copies of the map at low zoom levels. Default `false`.
    """

    near_z_multiplier = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Scaler for the near plane, 1 unit equals to the height of the viewport.

    Default to `0.1`. Overwrites the `near` parameter.
    """

    far_z_multiplier = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Scaler for the far plane, 1 unit equals to the distance from the camera to the top edge of the screen.

    Default to `1.01`. Overwrites the `far` parameter.
    """

    projection_matrix = t.List(
        t.Float(),
        allow_none=True,
        default_value=None,
        minlen=16,
        maxlen=16,
    ).tag(
        sync=True,
    )
    """Projection matrix.

    If `projectionMatrix` is not supplied, the `View` class will build a projection matrix from the following parameters:
    """

    fovy = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Field of view covered by camera, in the perspective case. In degrees.

    If not supplied, will be calculated from `altitude`.
    """

    altitude = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of the camera relative to viewport height.

    Default `1.5`.
    """

    orthographic = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to create an orthographic or perspective projection matrix.

    Default is `false` (perspective projection).
    """


class GlobeView(BaseView):
    """A deck.gl GlobeView.

    [deck-globe-view]: https://deck.gl/docs/api-reference/core/globe-view

    The `GlobeView` projects the earth into a 3D globe.
    """

    _view_type = t.Unicode("globe-view").tag(sync=True)

    _view_state_type = GlobeViewState

    resolution = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """The resolution at which to turn flat features into 3D meshes, in degrees.

    Smaller numbers will generate more detailed mesh. Default `10`.
    """

    near_z_multiplier = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Scaler for the near plane, 1 unit equals to the height of the viewport.

    Default to `0.1`. Overwrites the `near` parameter.
    """

    far_z_multiplier = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Scaler for the far plane, 1 unit equals to the distance from the camera to the top edge of the screen.

    Default to `2`. Overwrites the `far` parameter.
    """


class FirstPersonView(BaseView):
    """A deck.gl FirstPersonView.

    The `FirstPersonView` class is a subclass of `View` that describes a camera placed at a provided location, looking towards the direction and orientation specified by viewState. The behavior is similar to that of a first-person game.
    """

    _view_type = t.Unicode("first-person-view").tag(sync=True)

    _view_state_type = FirstPersonViewState

    projection_matrix = t.List(
        t.Float(),
        allow_none=True,
        default_value=None,
        minlen=16,
        maxlen=16,
    ).tag(
        sync=True,
    )
    """Projection matrix.

    If `projectionMatrix` is not supplied, the `View` class will build a projection matrix from the following parameters:
    """

    fovy = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Field of view covered by camera, in the perspective case. In degrees.

    Default `50`.
    """

    near = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of near clipping plane.

    Default `0.1`.
    """

    far = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of far clipping plane.

    Default `1000`.
    """

    focal_distance = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Modifier of viewport scale.

    Corresponds to the number of pixels per meter. Default `1`.
    """


class OrbitView(BaseView):
    """A deck.gl OrbitView.

    The `OrbitView` class is a subclass of `View` that creates a 3D camera that rotates around a target position. It is usually used for the examination of a 3D scene in non-geospatial use cases.
    """

    _view_type = t.Unicode("orbit-view").tag(sync=True)

    _view_state_type = OrbitViewState

    orbit_axis = t.Unicode(allow_none=True, default_value=None).tag(sync=True)
    """Axis with 360 degrees rotating freedom, either `'Y'` or `'Z'`, default to `'Z'`."""

    projection_matrix = t.List(
        t.Float(),
        allow_none=True,
        default_value=None,
        minlen=16,
        maxlen=16,
    ).tag(
        sync=True,
    )
    """Projection matrix.

    If `projectionMatrix` is not supplied, the `View` class will build a projection matrix from the following parameters:
    """

    fovy = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Field of view covered by camera, in the perspective case. In degrees.

    Default `50`.
    """

    near = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of near clipping plane.

    Default `0.1`.
    """

    far = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of far clipping plane.

    Default `1000`.
    """

    orthographic = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to create an orthographic or perspective projection matrix.

    Default is `false` (perspective projection).
    """


class OrthographicView(BaseView):
    """A deck.gl OrthographicView.

    The `OrthographicView` class is a subclass of `View` that creates a top-down view of the XY plane. It is usually used for rendering 2D charts in non-geospatial use cases.
    """

    _view_type = t.Unicode("orthographic-view").tag(sync=True)

    _view_state_type = OrthographicViewState

    flip_y = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """
    Whether to use top-left coordinates (`true`) or bottom-left coordinates (`false`).

    Default `true`.
    """

    near = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of near clipping plane.

    Default `0.1`.
    """

    far = t.Float(allow_none=True, default_value=None).tag(sync=True)
    """Distance of far clipping plane.

    Default `1000`.
    """

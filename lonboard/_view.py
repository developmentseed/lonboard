import traitlets as t

from lonboard._base import BaseWidget

# class View(BaseWidget):


class GlobeView(BaseWidget):
    _view_type = t.Unicode("globe").tag(sync=True)

    resolution = t.Float(
        10.0,
        help="The resolution at which to turn flat features into 3D meshes, in degrees. Smaller numbers will generate more detailed mesh.",
    ).tag(sync=True)
    """The resolution at which to turn flat features into 3D meshes, in degrees.

    Smaller numbers will generate more detailed mesh. Default 10.
    """

    # nearZMultiplier (number, optional)
    # Scaler for the near plane, 1 unit equals to the height of the viewport. Default to 0.1. Overwrites the near parameter.

    # farZMultiplier (number, optional)
    # Scaler for the far plane, 1 unit equals to the distance from the camera to the edge of the screen. Default to 2. Overwrites the far parameter.

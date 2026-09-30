# Jupyter Widgets

[Jupyter Widgets](https://ipywidgets.readthedocs.io/en/stable/) are interactive browser controls for Jupyter notebooks. While Lonboard's classes are themselves widgets, Jupyter Widgets' design means that widgets integrate with other widgets seamlessly.

For example, the `ipywidgets` Python library [includes many core widgets](https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20List.html) like sliders, dropdowns, color pickers, and file upload elements. Then you can [_link widgets together_](https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20Events.html#linking-widgets). This means that your widget-based slider or chart can create events that change the display of a Lonboard map based on user input events.

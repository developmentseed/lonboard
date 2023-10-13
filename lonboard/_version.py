from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lonboard")
except PackageNotFoundError:
    __version__ = "uninstalled"

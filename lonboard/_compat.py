def check_pandas_version():
    import pandas as pd

    if int(pd.__version__[0]) < 2:
        raise ValueError("Pandas v2 or later is required.")

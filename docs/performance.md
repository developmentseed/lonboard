# Performance

Performance is a critical goal of lonboard. Below are a couple pieces of information you should know to understand lonboard's performance characteristics, as well as some advice for how to get the best performance.

## Performance Characteristics

There are two distinct parts to the performance of **lonboard**: one is the performance of transferring data to the browser and the other is the performance of rendering the data once it's there.

In general, these parts are completely distinct. Even if it takes a while to load the data in your browser, the map might be snappy once it loads, and vice versa.

### Data Transfer

Lonboard creates an interactive visualization of your data in your browser. In order to do this, your GeoDataFrame needs to be transferred from your Python environment to your browser.

In the case where your Python session is running locally (on the same machine as your browser), this data transfer is extremely fast: less than a second in most cases.

However, in the case where your Python session is running on a remote server (such as [Google Colab](https://colab.research.google.com/), [Binder](https://mybinder.readthedocs.io/en/latest/introduction.html), or a JupyterHub instance), this data transfer means **downloading the data to your local browser**. Therefore, when running lonboard from a remote server, your internet speed and the quantity of data you pass into a layer will have large impacts on the data transfer speed.

Under the hood, lonboard uses efficient compression (in the form of [GeoParquet](https://geoparquet.org/)) to transfer data to the browser, but compression can only do so much; the data still needs to be downloaded.

### Rendering Performance

Once the data has been transfered from your Python session to your browser, it needs to be rendered.

The biggest thing to note is that — in contrast to projects like [datashader](https://datashader.org/) — lonboard **does not minimize the amount of data being rendered**. If you pass a GeoDataFrame with 10 million coordinates, lonboard will attempt to render all 10 million coordinates at once.

The primary determinant of the maximum amount of data you can render with lonboard is your computer's hardware. Via the underlying [deck.gl](https://deck.gl/) library, lonboard ultimately renders geometries using your computer's Graphics Processing Unit (GPU). If you have a better GPU card, you'll be able to visualize more data.

Lonboard is more efficient at rendering than previous libraries, but there will always be _some quantity of data_ beyond which your browser tab is likely to crash while attempting to render. Testing on a recent MacBook Pro M2 computer, lonboard has been able to render a few million points with minimal lag.

## Performance Advice

### Use a local Python session

Moving from a remote Python environment to a local Python environment is often impractical, but this change will make it much faster to visualize data, especially over slow internet connections.

### Remove columns before rendering

All columns included in the `GeoDataFrame` will be transferred to the browser for visualization. (In the future, these other columns will be used to display a tooltip when hovering over/clicking on a geometry.)

Especially in the case of a remote Python session, excluding unnecessary attribute columns will make data transfer to the browser faster.

### Use Arrow-based data types in Pandas

As of Pandas 2.0, Pandas supports two backends for data types: either the original numpy-based data types or new data types based on Arrow and the pyarrow library.

The first thing that lonboard does when visualizing data is converting from Pandas to an Arrow representation. Any non-geometry attribute columns will be converted to Arrow, so if you're using Arrow-based data types in Pandas already, this step will be "free" as no conversion is needed.

See the pandas [guide on data types](https://pandas.pydata.org/docs/user_guide/pyarrow.html) and the [`pandas.ArrowDtype` class](https://pandas.pydata.org/docs/reference/api/pandas.ArrowDtype.html).

### Simplify geometries before rendering

Simplifying geometries before rendering reduces the total number of coordinates and can make a visualization snappier. At this point, lonboard does not offer built-in geometry simplification. This is something you would need to do before passing data to lonboard.

# Build instructions for the documentation

## General points

The documentation is built automatically using Sphinx.
The following Python packages are needed for a successful build:

* Sphinx
* sphinx-autodoc-typehints
* sphinx-rtd-theme

Besides the above, you would also need GNU make (as well as coreutils) to run
the build in a convenient way.

## Building

To build the documentation run:

`make html`

The resulting pages would be generated under _html/_ subfolder

To remove the old html files run:

`make clean`

(This is performed automatically before each build)

To generated new templates for API docs run:

`make apidocs`

The resulting RST files would be created under _PyLabware_ subdirectory.

# Requirements

## Runtime

- Python 3.11 or newer.
- The mdoc package, installed in a Python environment accessible from your terminal.
- `markdown-it-py`, `mdit-py-plugins` and `PyYAML`, installed automatically with mdoc.
- Windows, macOS or Linux. Document source files use UTF-8.

The installed command must be available on `PATH` or called by its full path.
If installed in a virtual environment, activate it or call its executable directly.
One installation can serve multiple document projects.

## Installation

To install a wheel from a GitHub release, download `mdoc-0.1.0-py3-none-any.whl`
and run this command from the directory containing the downloaded file:

```sh
python -m pip install ./mdoc-0.1.0-py3-none-any.whl
```

To install from a source checkout, run this from the repository root:

```sh
python -m pip install .
```

To build a wheel from the source checkout, install the build tool and run:

```sh
python -m pip install build
python -m build --wheel
```

The wheel is written to `dist/` and can be attached to a GitHub release.

## PDF Dependencies

PDF additionally requires WeasyPrint and native libraries, including Pango.
PDF cover assembly uses pypdf, included in the `pdf` extra.
HTML, Markdown, initialization and help do not require those components.
Platform-specific requirements are described in the PDF Rendering section.

## Development

- `setuptools` is the package build backend.
- The `dev` extra supplies `pytest` and `pypdf` for the test suite.
- Development uses an editable installation: `python -m pip install -e ".[dev]"`.
- Run tests with `python -m pytest -q`.
- The `pdf` extra supplies WeasyPrint and pypdf but does not install native libraries.

A standalone executable and installer are not available; install mdoc with pip.
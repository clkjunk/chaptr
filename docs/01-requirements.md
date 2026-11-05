# Requirements

## Runtime

- Python 3.11 or newer.
- The mdoc package, installed in a Python environment accessible from your terminal.
- `markdown-it-py`, `mdit-py-plugins` and `PyYAML`, installed automatically with mdoc.
- Windows, macOS or Linux. Document source files use UTF-8.

The installed command must be available on `PATH` or called by its full path.
If installed in a virtual environment, activate it or call its executable directly.
One installation can serve multiple document projects.

## PDF Dependencies

PDF additionally requires WeasyPrint and native libraries, including Pango.
HTML, Markdown, initialization and help do not require those components.
Platform-specific requirements are described in the PDF Rendering section.

## Development

- `setuptools` is the package build backend.
- The `dev` extra supplies `pytest` for the test suite.
- Development uses an editable installation: `python -m pip install -e ".[dev]"`.
- Run tests with `python -m pytest -q`.
- The `pdf` extra supplies WeasyPrint but does not install its native libraries.

A self-contained executable and installer are not available yet.
# PDF Rendering

mdoc renders the configured Markdown to HTML, applies CSS and passes that document
to WeasyPrint for PDF generation.

```sh
mdoc build --format pdf
```

## Requirements

The optional `pdf` extra supplies WeasyPrint. For development in the application
repository, install it with `python -m pip install -e ".[pdf]"`.
For a wheel installation, request its extra:

```sh
python -m pip install "path/to/mdoc-0.1.0-py3-none-any.whl[pdf]"
```

WeasyPrint also needs native system libraries, including Pango. These are compiled
components for font handling and text layout.
Installing the Python extra alone may not be sufficient.

Follow the current [WeasyPrint platform requirements](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)
for Windows, macOS or Linux.

## Current Status

The PDF build path is implemented. On the initial Windows development machine,
generation was blocked by missing `libgobject-2.0-0`. Successful PDF rendering and
a clean-machine installation have not yet been verified.

Missing renderer dependencies produce a build error. HTML and Markdown output,
initialization and help remain available without them.

Self-contained releases are planned to bundle Python, WeasyPrint and native
libraries so users do not need separate setup. Those bundles are not implemented
or verified yet. The current wheel requires Python.
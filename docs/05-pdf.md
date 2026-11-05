# PDF Rendering

mdoc renders the configured Markdown to HTML, applies CSS and passes that document
to WeasyPrint for PDF generation.

```sh
mdoc build --format pdf
```

## Requirements

The optional `pdf` extra supplies WeasyPrint and pypdf. For development in the application
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

## PDF Covers

Export a single-page PDF for each cover from your design tool, then configure:

```yaml
front_cover: covers/front.pdf
back_cover: covers/back.pdf
```

Either cover is optional. Paths are relative to the project configuration.
Build with `mdoc build --format pdf` to combine the front cover, generated content
and back cover into one PDF. A cover can also be Markdown; mixed types work.

PDF covers retain their artwork, fonts and page content. Generated content margins
and theme CSS do not add borders to them. Export the design to the page edges for
an edge-to-edge cover. Covers are not scaled or cropped during assembly.

Each PDF cover must be unencrypted and contain exactly one page. Its page size
must match the adjacent generated page, allowing a rounding difference of one
PDF point. An A4 document needs A4 covers; a landscape cover needs matching
document orientation. Invalid covers fail the build before existing output is
replaced. Source cover files cannot also be the output document.

The final PDF keeps the generated document's title metadata, bookmarks and linked
destinations. An inserted front cover counts as page 1, so contents page numbers
match the final PDF's physical pages. Avoid overriding the PDF page counter in
custom themes when using this numbering scheme.

HTML and Markdown builds omit PDF covers. They can still be used to preview and
edit the content. The docs project keeps Markdown covers as its editable default.
Print-production bleed and trim configuration are not provided.

## Current Status

PDF generation has been checked on the Windows development setup, including
document pages, captions, notes, PDF covers and contents page numbers. A clean-machine
installation has not yet been verified.

Missing renderer dependencies produce a build error. HTML and Markdown output,
initialization and help remain available without them.

Self-contained releases are planned to bundle Python, WeasyPrint and native
libraries so users do not need separate setup. Those bundles are not implemented
or verified yet. The current wheel requires Python.
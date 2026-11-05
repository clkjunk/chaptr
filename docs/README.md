# Documentation

- [Requirements](01-requirements.md)
- [User Workflow](02-workflow.md)
- [Configuration and Variables](03-configuration.md)
- [Themes](04-themes.md)
- [PDF Rendering](05-pdf.md)
- [Current Limitations](06-limitations.md)
- [Roadmap](07-roadmap.md)

These sections form a document project. Its
[configuration](document.yaml) defines their order and shared values; its
[stylesheet](styles.css) customizes the bundled theme.

The configured [front cover](00-front-cover.md), [author section](00-authors.md)
and [back cover](99-back-cover.md) demonstrate optional pages. The build also
generates a title page and contents. Captions and footnotes are demonstrated in
[Configuration and Variables](03-configuration.md).

`mdoc init` creates an editable copy of this documentation as its default project.
From that project directory (or this documentation directory), run:

```sh
mdoc build
mdoc build --format markdown
mdoc build --format pdf
```

PDF requires the dependencies described in [PDF Rendering](05-pdf.md).
Open `build/document.html` directly in a browser or use the generated PDF.

From the application repository root, use `mdoc build --config docs/document.yaml`.

For this checkout's environment on Windows, without activation:

```powershell
.\.venv\Scripts\mdoc.exe build --config docs/document.yaml
```

The terminal manual is available through `mdoc help`.
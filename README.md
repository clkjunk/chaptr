# mdoc

Turn separate Markdown chapters into one document, with shared variables and
editable themes. Produce merged Markdown, styled HTML or PDF.

## Usage

mdoc runs in your terminal. Install it once and use it across document projects.

| Command | Purpose |
| --- | --- |
| `mdoc init [directory]` | Create an editable copy of the app's documentation |
| `mdoc build` | Build the current project; HTML is the default |
| `mdoc build --format pdf` | Generate PDF when renderer dependencies are available |
| `mdoc help` | Read the bundled command manual |
| `mdoc --help` | List commands; each command also supports `--help` |

See the [documentation](docs/README.md) for requirements, the user workflow,
configuration, themes and current limitations. The documentation is itself an
mdoc project, so you can try the tool on its own source:

```sh
mdoc build --config docs/document.yaml
```

## Changelog

### 0.1.0 - Unreleased

- Project initialization with the app's documentation and overwrite protection.
- Ordered Markdown chapters and simple shared variables.
- Markdown and HTML output, with an optional WeasyPrint PDF renderer.
- Bundled themes, project-local overrides and additional stylesheets.
- Command help and a bundled usage manual.

Self-contained releases are not available yet; PDF requires native libraries.

Planned: [named document templates](docs/07-roadmap.md), including roleplaying
scenarios and workplace accessibility documents. Template selection is not available yet.
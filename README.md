# chaptr

Turn separate Markdown chapters into one document, with shared variables and
editable themes. Produce merged Markdown, styled HTML or PDF.

## Usage

chaptr runs in your terminal. Install it once and use it across document projects.
See [installation instructions](docs/01-requirements.md#installation) for the
source checkout and GitHub release wheel options.

| Command | Purpose |
| --- | --- |
| `chaptr init [directory]` | Create an editable copy of the app's documentation |
| `chaptr build` | Build the current project; HTML is the default |
| `chaptr build --format pdf` | Generate PDF when renderer dependencies are available |
| `chaptr help` | Read the bundled command manual |
| `chaptr --help` | List commands; each command also supports `--help` |
| `chaptr themes list` | Browse community themes |
| `chaptr themes add THEME` | Install a theme into the current document project |

See the [documentation](docs/README.md) for requirements, the user workflow,
configuration, themes and current limitations. The documentation is itself a
chaptr project, so you can try the tool on its own source:

```sh
chaptr build --config docs/document.yaml
```

## Changelog

### 0.1.2

- Added bottom-right PDF page numbers starting after covers and title pages, with matching contents references and configurable footers.
- Added paper-size presets shared by HTML previews and PDFs, plus opt-in Polish single-letter word spacing through `language: pl`.
- Replaced modern and vintage with a neutral base theme, reusable columns and alignment utilities. Existing projects using those bundled names should select `base` or install a custom theme.
- Added commands to browse, install and update community themes.
- Added MIT licensing to the repository and package metadata.

### 0.1.1

- Renamed the package and command to chaptr.
- Added publishing to PyPI through GitHub Actions Trusted Publishing.

### 0.1.0

- Project initialization with the app's documentation and overwrite protection.
- Ordered Markdown chapters and simple shared variables.
- Automatic table captions, linked footnotes and a table of contents.
- Optional title pages, covers and author sections.
- Pre-designed PDF covers with page-size validation and preserved contents links.
- Markdown and HTML output, with an optional WeasyPrint PDF renderer.
- Bundled themes, project-local overrides and additional stylesheets.
- Command help and a bundled usage manual.

PDF requires native libraries.

Planned: [named document templates](docs/07-roadmap.md), including accessibility-oriented
documents. Template selection is not available yet.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
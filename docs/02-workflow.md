# User Workflow

Use $app_name $app_version to create a document, edit its source files and rebuild
whenever the content changes.

## Create a Project

```sh
mdoc init my-document
cd my-document
```

Or run `mdoc init` inside the directory you want to use. Initialization is
noninteractive. Its default content is $app_name's own documentation: the section
files, `README.md`, `document.yaml` and `styles.css`, plus a `.gitignore` that
excludes generated build output. The files come bundled with the CLI.

Open `README.md` to read the documentation or run `mdoc build` to render it.
Replace the sections with your own content when ready.

Existing starter files are never overwritten. Conflicts stop initialization
before files are written; unrelated files are kept. There is no force option.

## Edit the Content

1. Set shared values in the configuration's `variables` mapping.
2. Edit the Markdown chapters with any text editor.
3. Add new chapter paths to `files` in the order they should appear.
4. Select a theme or adjust the project stylesheet when needed.

Rename or replace the documentation sections and update `files` accordingly.
Named project templates are future work; `init` currently has one default only.

## Build

```sh
mdoc build
mdoc build --format markdown
mdoc build --format pdf
```

The default format is HTML. PDF needs the additional renderer dependencies.
The output directory is created on the first build and receives `document.html`,
`document.md` or `document.pdf`. Rebuilding a format replaces its previous file;
other formats are untouched. Successful builds print the output path.

Open HTML directly in a browser.

## Work from Another Directory

```sh
mdoc build --config "path/to/my-document/document.yaml"
```

Without `--config`, mdoc uses `document.yaml` in the current directory.
All configured paths are resolved relative to that YAML file. Quote paths
containing spaces.

## Get Help

```sh
mdoc --help
mdoc init --help
mdoc build --help
mdoc help
```

Exit codes are `0` for success, `1` for initialization or build errors and `2`
for invalid command-line usage. Help works without a document project.
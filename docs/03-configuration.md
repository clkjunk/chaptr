# Configuration and Variables

Each document project has a YAML configuration. Only `files` is required.[^paths]

```yaml
title: Product Guide
theme: modern
stylesheet: styles.css
output: build
files:
  - chapters/01-introduction.md
  - chapters/02-requirements.md
variables:
  product_name: Field Notes
  version: "1.0"
```

## Fields

Table: Configuration fields

| Field | Meaning | Default |
| --- | --- | --- |
| `files` | Nonempty list of Markdown paths, in chapter order | Required |
| `title` | HTML document title | Document |
| `theme` | Named CSS theme for HTML and PDF | modern |
| `stylesheet` | Extra project CSS applied after the theme | None |
| `output` | Directory for generated files | build |
| `variables` | Shared text, numeric or boolean values | Empty mapping |
| `title_page` | Generate a title page using title, subtitle and author | false |
| `subtitle` | Subtitle on the generated title page | Empty |
| `author` | Author text on the generated title page | Empty |
| `front_cover` | Markdown file for a separate front cover | None |
| `author_section` | Markdown file for author details | None |
| `table_of_contents` | Generate linked contents with PDF page numbers | false |
| `toc_depth` | Heading levels included in contents, from 1 to 6 | 2 |
| `back_cover` | Markdown file for a separate back cover | None |

Configured paths are relative to the configuration file. To use a different
configuration filename, pass its path with `--config`.

## Variables

Reference a shared value using `$product_name`:

```markdown
# $product_name

Product guide, version $version.
```

Names contain letters, digits or underscores and cannot begin with a digit.
Undefined names stop the build with a source filename and line number.
Values are inserted as Markdown, so they may affect the rendered formatting.

Write `$$` for a literal dollar sign: `$$20` becomes `$20` in ordinary text.
Code blocks and ordinary inline code retain their original contents.
Multiline inline code is a current exception.

Only variable substitution is supported.

## Table Captions

Place a standalone `Table: Caption text` paragraph directly above or below a table:

```markdown
Table: Release formats

| Format | Extension |
| --- | --- |
| HTML | .html |
| PDF | .pdf |
```

Captions become `Table 1. Release formats`, numbered across the document in chapter
order. Moving or inserting captioned tables updates their numbers. Tables without
captions stay unnumbered. Use one caption per table. Caption text supports inline
Markdown. A caption below the source table is displayed below it.

## Footnotes

Use Markdown footnote references and definitions:

```markdown
An explanation with a note.[^detail]

[^detail]: Additional information with **formatting**.
```

Notes are numbered by first reference across the document and collected in a
linked Notes section before the back cover. References and definitions can be in
different chapters; use unique labels throughout the project. Notes currently
appear at the end of the document, not at the bottom of individual PDF pages.

## Document Pages

```yaml
title: Product Guide
subtitle: Release documentation
author: Example Author
title_page: true
front_cover: front-cover.md
author_section: authors.md
table_of_contents: true
toc_depth: 2
back_cover: back-cover.md
```

All these options are optional. Page order is front cover, title page, author
section, contents, chapters, notes and back cover. Cover and author files contain
ordinary Markdown and support variables and images. Do not list them again in
`files`. The title, subtitle and author fields are plain text.

Contents include chapter headings up to `toc_depth`. Duplicate heading names get
unique IDs such as `requirements` and `requirements-2`. HTML contents use links;
PDF contents also show page numbers.

HTML and PDF generate title pages, contents and numbered captions. Merged Markdown
includes the authored cover and author sections and preserves caption and footnote
syntax. It does not generate title-page or contents markup.

[^paths]: Source and output paths are resolved relative to the configuration file.
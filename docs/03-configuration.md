# Configuration and Variables

Each document project has a YAML configuration. Only `files` is required.[^paths]

```yaml
title: Product Guide
language: en
page_size: A4
theme: base
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
| `language` | Document language tag; `pl` enables Polish word spacing | en |
| `page_size` | Paper preset: A3, A4, A5, Letter or Legal | A4 |
| `theme` | Named CSS theme for HTML and PDF | base |
| `stylesheet` | Extra project CSS applied after the theme | None |
| `output` | Directory for generated files | build |
| `variables` | Shared text, numeric or boolean values | Empty mapping |
| `title_page` | Generate a title page using title, subtitle and author | false |
| `subtitle` | Subtitle on the generated title page | Empty |
| `author` | Author text on the generated title page | Empty |
| `front_cover` | Markdown or single-page PDF front cover | None |
| `author_section` | Markdown file for author details | None |
| `table_of_contents` | Generate linked contents with PDF page numbers | false |
| `toc_depth` | Heading levels included in contents, from 1 to 6 | 2 |
| `back_cover` | Markdown or single-page PDF back cover | None |

Configured paths are relative to the configuration file. To use a different
configuration filename, pass its path with `--config`.

## Paper Size

Set `page_size` to use the same paper dimensions for PDF and the continuous HTML
preview. Sizes are portrait and names are case-sensitive:

| Preset | Width | Height |
| --- | ---: | ---: |
| A3 | 297mm | 420mm |
| A4 | 210mm | 297mm |
| A5 | 148mm | 210mm |
| Letter | 215.9mm | 279.4mm |
| Legal | 215.9mm | 355.6mm |

The base style uses 20mm print margins. On a wide screen, the HTML document has
the selected paper width, including 20mm padding on each side. It remains a
continuous document without simulated page boundaries. On smaller screens it
fits the viewport and uses reduced padding on phones. Browser zoom and installed
fonts can affect its appearance; the PDF determines the final pagination.

## Language and Word Spacing

For a Polish document, configure:

```yaml
language: pl
page_size: A4
```

`pl` and regional tags such as `pl-PL` keep the single-letter words `a`, `i`, `o`,
`u`, `w` and `z` with the following word by inserting nonbreaking spaces in
rendered HTML and PDF. Uppercase forms and words preceded by opening quotes or
brackets are supported, including across emphasis and link formatting. For
example, `W domu i w ogrodzie` keeps `W` with `domu` and `i w` with `ogrodzie`.

The rule applies to prose, headings, tables, notes, contents entries and generated
title-page text. Code, image descriptions, link destinations and displayed URL
autolinks are left unchanged. Ordinary Markdown line breaks are treated as spaces;
explicit hard line breaks are preserved. Source files and merged Markdown are
never changed by the rule. Other languages currently receive no automatic
single-letter spacing adjustments.

The language tag also sets the HTML document's `lang` attribute. This typography
rule is separate from CSS widow and orphan control, which manages how paragraph
lines are divided across printed pages.

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
section, contents, chapters, notes and back cover. Markdown covers and author files
support variables and images. Do not list them again in `files`. The title,
subtitle and author fields are plain text.

For externally designed covers:

```yaml
front_cover: covers/front.pdf
back_cover: covers/back.pdf
```

PDF covers must be unencrypted single-page files matching the generated page size.
They are attached unchanged to the final PDF. HTML and Markdown builds omit them.
See [PDF Rendering](05-pdf.md) for validation and page-numbering details.

Contents include chapter headings up to `toc_depth`. Duplicate heading names get
unique IDs such as `requirements` and `requirements-2`. HTML contents use links;
PDF contents also show printed page numbers. Base styling removes link underlines
from contents. Printed numbering begins at 1 on the author section, or contents
or the first chapter when authors are absent; front covers and title pages do
not count towards it. See [Themes](04-themes.md) for footer customization.

HTML and PDF generate title pages, contents and numbered captions. Merged Markdown
includes Markdown cover and author sections and preserves caption and footnote
syntax. It does not generate title-page or contents markup.

[^paths]: Source and output paths are resolved relative to the configuration file.
# Themes

Chaptr bundles one neutral `base` stylesheet: black text, Helvetica with sans-serif
fallbacks, 12pt type and 1.5 line spacing. It provides headings, images, tables,
columns, alignment and print layout. Optional themes add a distinct visual style
on top of this foundation.

Existing projects using the removed bundled `modern` or `vintage` themes should
change their configuration to `theme: base`. Project-local themes still work,
including any local themes that use those names.

## Choose a Theme

Omit `theme` or set `theme: base` for the neutral document. Override it for one build:

```sh
chaptr build --theme base
```

Theme selection applies to HTML and PDF.

## Community Themes

From a document project's directory, use the `themes` commands to browse the
public Chaptr theme catalog, inspect a theme or install it:

```sh
chaptr themes list
chaptr themes info roleplaying
chaptr themes add roleplaying
```

These commands need an internet connection. Installing a theme copies its CSS,
README and license into `themes/<theme-id>/` and records its version. Set
`theme: roleplaying` in `document.yaml` to use it. Existing local themes are
never replaced by `add`.

Check installed community themes for newer catalog versions and update one
explicitly:

```sh
chaptr themes check
chaptr themes update roleplaying
```

An update replaces the installed theme directory, including its CSS and other
downloaded files. Keep personal changes in the project's separate `stylesheet`
file; it remains in place when the theme is updated. Themes that were added by
hand are not tracked or updated by these commands.

The catalog is maintained in the public
[chaptr-themes repository](https://github.com/clkjunk/chaptr-themes). It may be
empty until themes are published. Project builds use already-installed files and
do not need to access the catalog.

To contribute a community theme, follow the repository's
[theme directory guide](https://github.com/clkjunk/chaptr-themes/blob/main/themes/README.md)
and submit a pull request using
[GitHub's contribution workflow](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project).

## Customize

For small adjustments, create a project stylesheet and configure
`stylesheet: styles.css`:

```css
body {
	font-family: Georgia, serif;
	font-size: 11pt;
	line-height: 1.6;
}

@page {
	size: A4;
	margin: 25mm;
}
```

For a complete theme, create `themes/company.css` or
`themes/company/company.css` and configure `theme: company`. Layout utilities
remain available to every theme. A local `themes/base.css` or
`themes/base/base.css` adds project rules after the bundled foundation.

Styling is applied in this order:

1. Shared application base CSS.
2. The project-local named theme, if selected. Plain `base` needs no extra theme.
3. The optional configured stylesheet.

## Print Styling

The base print layout defaults to A4 pages, 20mm margins and a page break between
chapters. Set `page_size` in the configuration to select A3, A4, A5, Letter or
Legal for both PDF and the continuous HTML preview's width.
Use `@page` for custom print settings and `@media print` for print-only rules.
Fonts must be available on the rendering machine or supplied as local font assets.

The generated CSS supplies `--page-width`, `--page-height` and
`--page-content-height` (paper height minus the default top and bottom margins).
If custom CSS changes paper dimensions or margins, keep the preview's width and
padding and the title page's minimum height consistent with those changes.

HTML and PDF share CSS, but browser and WeasyPrint support differ. Keep print CSS
conservative and verify the actual PDF. Relative CSS asset URLs currently resolve
from the document project's root.

## Document Elements

Use `caption` to style table labels. Their top or bottom placement follows the
caption's source position. `.front-cover`, `.title-page`, `.author-section`,
`.contents` and `.back-cover` style the optional document pages.

```css
caption {
	color: #24634b;
	font-size: 10pt;
}

.title-page {
	text-align: center;
}

.footnotes {
	font-size: 9pt;
}
```

The base print theme starts each optional page separately. Contents page numbers
use WeasyPrint's `target-counter` support. Custom themes can override these rules.
External PDF covers keep their own styling; theme rules apply to generated pages.

## Page Numbers

The base print layout places page numbers at the bottom right, starting at 1 on
the author section. Without an author section, numbering starts on contents or
the first chapter. Front covers and title pages do not count towards printed
numbering. The back cover has no generated number. Contents links remain active
without underlines and their page references match the printed numbers.

Customize the footer in the project stylesheet, for example:

```css
:root {
	--page-number-content: "Page " counter(page);
}
```

Set `--page-number-content: none` to hide numbers. To move them to the center,
override the page margin boxes:

```css
@page {
	@bottom-right {
		content: none;
	}

	@bottom-center {
		content: var(--page-number-content, counter(page));
	}
}

@page front-matter {
	@bottom-center {
		content: none;
	}
}

@page back-cover {
	@bottom-center {
		content: none;
	}
}
```

Keep suppression rules for the `front-matter` and `back-cover` named pages when
changing footer positions. Page numbers are print-only; the continuous HTML
preview does not display page footers.

## Classed Containers

Wrap Markdown in a classed container to give a theme-specific block a CSS hook:

```markdown
::: note-panel toc=exclude
## Panel heading

Content for the panel.
:::
```

The class names are applied to a generated `div`. The optional `toc=exclude`
flag keeps headings inside the container out of the generated table of contents.
HTML and PDF render the container; Markdown output preserves its source syntax.
Raw HTML remains disabled.

## Columns

Use `columns` for two equal-width columns. Add a modifier for a different layout:

| Container classes | Column widths |
| --- | --- |
| `columns` | 1/2 and 1/2 |
| `columns columns-3` | 1/3, 1/3 and 1/3 |
| `columns columns-2-1` | 2/3 and 1/3 |
| `columns columns-1-2` | 1/3 and 2/3 |

Each `column` block holds ordinary Markdown, including headings, images and tables.
Use four colons for the outer block so the inner three-colon blocks nest correctly:

```markdown
:::: columns columns-2-1
::: column
## Main text

The wider column can contain several paragraphs.
:::

::: column
## Reference

![Map](img/map.png)

| Item | Cost |
| --- | ---: |
| Rope | 5 |
:::
::::
```

For three columns, use `columns columns-3` and include three `column` blocks.
Widths divide the space remaining after the gutters. These are independent
side-by-side blocks, not newspaper columns that automatically flow text between
them. Content reads in source order. Columns stack below 600px on screens and
retain their proportions in PDF and browser print output. Long columns may
continue onto another printed page; check the rendered PDF for pagination.

## Alignment and Images

Wrap content in `align-left`, `align-center`, `align-right` or `align-justify`:

```markdown
::: align-center
![Illustration](img/illustration.png)

Illustration caption.
:::
```

Left, center and right alignment also position images within the block. Images
keep their proportions and fit the available width. Combine alignment with a
column, for example `::: column align-right`. Use project CSS to set a specific
image width. Standard Markdown table alignment (`:---`, `:---:` and `---:`)
continues to control individual table columns.
# Themes

Themes are editable CSS. The application bundles `modern` and `vintage`; document
projects can replace either theme or define a new name without modifying the app.

## Choose a Theme

Set `theme: vintage` in the configuration or override it for one build:

```sh
chaptr build --theme vintage
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

## Customize

For small adjustments, create a project stylesheet and configure
`stylesheet: styles.css`:

```css
body { font-family: Georgia, serif; line-height: 1.75; }
th { background: #edf4f0; }
@page { size: A4; margin: 25mm; }
```

For a complete theme, create `themes/company.css` or
`themes/company/company.css` and configure `theme: company`. A local
`themes/modern.css` or `themes/modern/modern.css` replaces the bundled modern
theme only for that project. Default themes remain part of the installed
application.

Styling is applied in this order:

1. Shared application base CSS.
2. The project-local named theme or the bundled theme if no local replacement exists.
3. The optional configured stylesheet.

## Print Styling

The base print layout uses A4 pages, 20mm margins and a page break between chapters.
Use `@page` to adjust page size and margins and `@media print` for print-only rules.
Fonts must be available on the rendering machine or supplied as local font assets.

HTML and PDF share CSS, but browser and WeasyPrint support differ. Keep print CSS
conservative and verify the actual PDF. Relative CSS asset URLs currently resolve
from the document project's root.

## Document Elements

Use `caption` to style table labels. Their top or bottom placement follows the
caption's source position. `.front-cover`, `.title-page`, `.author-section`,
`.contents` and `.back-cover` style the optional document pages.

```css
caption { color: #24634b; font-size: 10pt; }
.title-page { text-align: center; }
.footnotes { font-size: 9pt; }
```

The base print theme starts each optional page separately. Contents page numbers
use WeasyPrint's `target-counter` support. Custom themes can override these rules.
External PDF covers keep their own styling; theme rules apply to generated pages.

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
# Themes

Themes are editable CSS. The application bundles `modern` and `vintage`; document
projects can replace either theme or define a new name without modifying the app.

## Choose a Theme

Set `theme: vintage` in the configuration or override it for one build:

```sh
mdoc build --theme vintage
```

Theme selection applies to HTML and PDF.

## Customize

For small adjustments, create a project stylesheet and configure
`stylesheet: styles.css`:

```css
body { font-family: Georgia, serif; line-height: 1.75; }
th { background: #edf4f0; }
@page { size: A4; margin: 25mm; }
```

For a complete theme, create `themes/company.css` and configure `theme: company`.
A local `themes/modern.css` replaces the bundled modern theme only for that
project. Default themes remain part of the installed application.

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
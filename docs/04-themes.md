# Themes

Themes are editable CSS. The application bundles `modern` and `vintage`; document
projects can replace either theme or define a new name without modifying the app.

## Choose a Theme

Set `theme: vintage` in the configuration or override it for one build:

```sh
chaptr build --theme vintage
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
External PDF covers keep their own styling; theme rules apply to generated pages.

## Editable Stat Blocks

Wrap ordinary Markdown in `::: monster` and a closing `:::` to render a
single-column stat block. Use an H2 for its name, an italic paragraph for its
description, a table for attributes and H3 headings for any ability sections.
Section names and statistics are not tied to a particular game system.

```markdown
::: monster
## Example Creature
*Medium humanoid*

**AC:** 12  
**HP:** 40

| STR | DEX | CON |
| --- | --- | --- |
| 9 (-1) | 14 (+2) | 11 (+0) |

### Actions
**Strike.** Write the complete action here.
:::
```

Include only the sections needed, such as actions, spells or reactions. Leave a
blank line between paragraphs; two trailing spaces create a line break within
a paragraph. The block's headings receive link targets but do not enter the
document table of contents. Keep the closing delimiter in the same chapter.

Style `.monster-card` in the project stylesheet. Override `--monster-accent`
and `--monster-rule` on that selector to change its colors. HTML and PDF render
the block; Markdown output preserves the source syntax. Raw HTML remains disabled.
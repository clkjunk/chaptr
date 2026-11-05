# Configuration and Variables

Each document project has a YAML configuration. Only `files` is required.

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

| Field | Meaning | Default |
| --- | --- | --- |
| `files` | Nonempty list of Markdown paths, in chapter order | Required |
| `title` | HTML document title | Document |
| `theme` | Named CSS theme for HTML and PDF | modern |
| `stylesheet` | Extra project CSS applied after the theme | None |
| `output` | Directory for generated files | build |
| `variables` | Shared text, numeric or boolean values | Empty mapping |

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
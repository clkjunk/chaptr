# Current Limitations

- Raw HTML in source Markdown and mathematical notation are not supported.
- Variable substitution does not yet preserve inline code spanning multiple lines.
- Cross-file Markdown links are not converted into internal document links.
- Footnotes are collected at the end of the document rather than at each PDF page's bottom.
- HTML/PDF resolve relative image and link targets against their source chapter.
  HTML references local files, which must remain available when opening the output.
- Merged Markdown retains original link paths. Relative assets may need path
  adjustments before the merged file is used elsewhere.
- Generated title pages, contents and numbered captions apply to HTML/PDF only.
- PDF covers are omitted from HTML and Markdown builds. They must be unencrypted
  single-page files matching the generated page size. Bleed and trim setup is not provided.
- Relative CSS asset URLs resolve from the project root.
- Browser and WeasyPrint CSS support differ; HTML preview does not prove PDF layout.
- PDF still requires native libraries and self-contained releases are not available.

Build trusted local projects only. PDF rendering can read local assets or fetch
remote URLs; this tool does not sandbox document projects.
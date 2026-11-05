import html
import re
from bisect import bisect_right
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin


def table_captions(tokens: list[Token], offsets: list[int]) -> None:
    number = 0
    index = 0
    while index < len(tokens):
        if tokens[index].type != "table_open":
            index += 1
            continue
        end = next(position for position in range(index + 1, len(tokens)) if tokens[position].type == "table_close")
        caption_start = None
        side = "top"
        for start, position in ((index - 3, "top"), (end + 1, "bottom")):
            paragraph = tokens[start:start + 3] if start >= 0 else []
            if (
                len(paragraph) == 3
                and [token.type for token in paragraph] == ["paragraph_open", "inline", "paragraph_close"]
                and paragraph[0].level == tokens[index].level
                and paragraph[1].content.startswith("Table: ")
                and paragraph[0].map and tokens[index].map
                and bisect_right(offsets, paragraph[0].map[0]) == bisect_right(offsets, tokens[index].map[0])
            ):
                caption_start = start
                side = position
                break
        if caption_start is None:
            index = end + 1
            continue
        caption = tokens[caption_start + 1]
        children = caption.children or []
        if not children or children[0].type != "text" or not children[0].content.startswith("Table: "):
            index = end + 1
            continue
        children[0].content = children[0].content[len("Table: "):]
        number += 1
        label = Token("text", "", 0)
        label.content = f"Table {number}. "
        caption.children = [label, *children]
        caption.content = label.content + caption.content[len("Table: "):]
        del tokens[caption_start:caption_start + 3]
        if side == "top":
            index -= 3
        tokens[index].attrSet("id", f"table-{number}")
        opening = Token("caption_open", "caption", 1)
        opening.attrSet("style", f"caption-side: {side}")
        tokens[index + 1:index + 1] = [opening, caption, Token("caption_close", "caption", -1)]
        index += 4


def render_document(chapters: list[tuple[str, Path, str]], config: dict) -> str:
    parser = MarkdownIt("commonmark", {"html": False}).enable("table").use(footnote_plugin)
    offsets = []
    sources = []
    line_number = 0
    for source, path, role in chapters:
        offsets.append(line_number)
        source = source.rstrip() + "\n\n"
        sources.append(source)
        line_number += source.count("\n")
    environment = {}
    tokens = parser.parse("".join(sources), environment)
    table_captions(tokens, offsets)
    groups = [[] for chapter in chapters]
    notes = []
    headings = []
    identifiers = {token.attrGet("id") for token in tokens if token.attrGet("id")}
    for token in tokens:
        if token.type == "footnote_open":
            note_number = token.meta["id"] + 1
            identifiers.update((f"fn{note_number}", f"fnref{note_number}"))
    owner = 0
    in_notes = False
    for index, token in enumerate(tokens):
        if token.type == "footnote_block_open":
            in_notes = True
        if not in_notes and token.map:
            owner = bisect_right(offsets, token.map[0]) - 1
        if token.type == "heading_open" and not in_notes:
            inline = tokens[index + 1]
            text = "".join(child.content for child in inline.children or [] if child.type in {"text", "code_inline", "image"})
            slug = re.sub(r"[^\w-]+", "-", text.lower()).strip("-") or "section"
            identifier = slug
            suffix = 2
            while identifier in identifiers:
                identifier = f"{slug}-{suffix}"
                suffix += 1
            identifiers.add(identifier)
            token.attrSet("id", identifier)
            if chapters[owner][2] == "chapter":
                headings.append((int(token.tag[1]), text, identifier))
        asset_owner = owner
        if in_notes and token.map:
            asset_owner = bisect_right(offsets, token.map[0]) - 1
        for child in token.children or []:
            attribute = "src" if child.type == "image" else "href" if child.type == "link_open" else None
            target = child.attrGet(attribute) if attribute else None
            if target:
                url = urlsplit(target)
                if not url.scheme and not url.netloc and url.path:
                    resolved = (chapters[asset_owner][1].parent / unquote(url.path)).resolve().as_uri()
                    if url.query:
                        resolved += "?" + url.query
                    if url.fragment:
                        resolved += "#" + url.fragment
                    child.attrSet(attribute, resolved)
        (notes if in_notes else groups[owner]).append(token)
    rendered = [parser.renderer.render(group, parser.options, environment) for group in groups]
    result = []
    for position, chapter in enumerate(chapters):
        if chapter[2] == "front-cover":
            result.append(f'<section class="front-cover document-page">{rendered[position]}</section>')
    if config.get("title_page"):
        title = html.escape(config.get("title", "Document"))
        subtitle = html.escape(config.get("subtitle", ""))
        author = html.escape(config.get("author", ""))
        result.append(
            f'<section class="title-page document-page"><h1>{title}</h1>'
            f'<p class="subtitle">{subtitle}</p><p class="author">{author}</p></section>'
        )
    for position, chapter in enumerate(chapters):
        if chapter[2] == "author-section":
            result.append(f'<section class="author-section document-page">{rendered[position]}</section>')
    if config.get("table_of_contents"):
        entries = "".join(
            f'<li class="toc-level-{level}"><a href="#{identifier}">{html.escape(text)}</a></li>'
            for level, text, identifier in headings if level <= config.get("toc_depth", 2)
        )
        result.append(f'<nav class="contents document-page" aria-label="Table of contents"><h1>Contents</h1><ol>{entries}</ol></nav>')
    for position, chapter in enumerate(chapters):
        if chapter[2] == "chapter":
            result.append(f'<section class="chapter">{rendered[position]}</section>')
    if notes:
        result.append('<section class="document-notes"><h2>Notes</h2>' + parser.renderer.render(notes, parser.options, environment) + "</section>")
    for position, chapter in enumerate(chapters):
        if chapter[2] == "back-cover":
            result.append(f'<section class="back-cover document-page">{rendered[position]}</section>')
    return "".join(result)
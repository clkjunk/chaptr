import argparse
import html
import re
import sys
from importlib.resources import files
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

from chaptr.render import render_document
from chaptr import theme_manager


class BuildError(ValueError):
    pass


def substitute(source: str, variables: dict[str, str], filename: Path) -> str:
    lines = source.splitlines(keepends=True)
    protected = set()
    for token in MarkdownIt().parse(source):
        if token.type in {"fence", "code_block"} and token.map:
            protected.update(range(*token.map))
    pattern = re.compile(r"\$\$|\$([A-Za-z_][A-Za-z0-9_]*)")

    def replace(match: re.Match[str], line_number: int) -> str:
        name = match.group(1)
        if name is None:
            return "$"
        if name not in variables:
            raise BuildError(f"{filename}:{line_number}: undefined variable ${name}")
        return variables[name]

    result = []
    for line_number, line in enumerate(lines, 1):
        if line_number - 1 in protected:
            result.append(line)
            continue
        parts = re.split(r"(`+[^`]*`+)", line)
        result.append("".join(
            part if index % 2 else pattern.sub(
                lambda match: replace(match, line_number), part
            )
            for index, part in enumerate(parts)
        ))
    return "".join(result)


def load_config(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise BuildError("Configuration must be a YAML mapping.")
    chapters = config.get("files")
    if not isinstance(chapters, list) or not chapters or not all(
        isinstance(chapter, str) for chapter in chapters
    ):
        raise BuildError("files must be a nonempty list of Markdown paths.")
    variables = config.get("variables", {})
    if not isinstance(variables, dict) or not all(
        isinstance(name, str)
        and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)
        and isinstance(value, (str, int, float, bool))
        for name, value in variables.items()
    ):
        raise BuildError("variables must map valid names to scalar values.")
    for name in ("title", "theme", "output", "stylesheet", "author", "subtitle", "front_cover", "back_cover", "author_section"):
        if name in config and not isinstance(config[name], str):
            raise BuildError(f"{name} must be a string.")
    for name in ("title_page", "table_of_contents"):
        if name in config and not isinstance(config[name], bool):
            raise BuildError(f"{name} must be true or false.")
    if "toc_depth" in config and (type(config["toc_depth"]) is not int or not 1 <= config["toc_depth"] <= 6):
        raise BuildError("toc_depth must be an integer from 1 to 6.")
    return config


def theme_css(root: Path, name: str, stylesheet: str | None) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise BuildError("theme must be a simple name, such as modern or vintage.")
    bundled = files("chaptr").joinpath("themes")
    local_directory = root / "themes" / name
    local_flat = root / "themes" / f"{name}.css"
    local_nested = local_directory / f"{name}.css"
    if local_flat.is_file():
        theme = local_flat
    elif local_nested.is_file():
        theme = local_nested
    else:
        theme = bundled.joinpath(f"{name}.css")
    if not theme.is_file():
        raise BuildError(f"Unknown theme: {name}")
    css = bundled.joinpath("base.css").read_text(encoding="utf-8")
    css += "\n" + theme.read_text(encoding="utf-8")
    if stylesheet:
        css += "\n" + (root / stylesheet).read_text(encoding="utf-8")
    return css


def build(config_path: Path, format_name: str = "html", theme: str | None = None) -> Path:
    config_path = config_path.resolve()
    root = config_path.parent
    config = load_config(config_path)
    variables = {name: str(value) for name, value in config.get("variables", {}).items()}
    chapters = []
    source_files = []
    pdf_covers = {
        field: root / config[field]
        for field in ("front_cover", "back_cover")
        if config.get(field) and Path(config[field]).suffix.lower() == ".pdf"
    }
    for field, role in (("front_cover", "front-cover"), ("author_section", "author-section")):
        if config.get(field) and field not in pdf_covers:
            source_files.append((config[field], role))
    source_files.extend((filename, "chapter") for filename in config["files"])
    if config.get("back_cover") and "back_cover" not in pdf_covers:
        source_files.append((config["back_cover"], "back-cover"))
    for filename, role in source_files:
        path = root / filename
        source = substitute(path.read_text(encoding="utf-8"), variables, path)
        chapters.append((source, path, role))
    output = root / config.get("output", "build")
    suffix = {"markdown": "md", "html": "html", "pdf": "pdf"}[format_name]
    destination = output / f"document.{suffix}"
    if format_name == "pdf" and any(path.resolve() == destination.resolve() for path in pdf_covers.values()):
        raise BuildError("A PDF cover cannot also be the output document. Choose a different cover path or output directory.")
    if format_name == "markdown":
        content = "\n\n".join(source.rstrip() for source, path, role in chapters) + "\n"
    else:
        css = theme_css(root, theme or config.get("theme", "modern"), config.get("stylesheet"))
        if format_name == "pdf" and "front_cover" in pdf_covers:
            css += "\n@page:first { counter-reset: page 2; }\n"
        title = html.escape(config.get("title", "Document"))
        content = (
            '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{title}</title><style>{css}</style></head>"
            f'<body><main>{render_document(chapters, config)}</main></body></html>\n'
        )
    if format_name == "pdf":
        try:
            from weasyprint import HTML
        except (ImportError, OSError) as error:
            raise BuildError(
                "PDF requires the pdf extra and WeasyPrint's native libraries. "
                "Run 'chaptr help' for PDF requirements. " + str(error)
            ) from error
        document = HTML(string=content, base_url=str(root)).write_pdf()
        if pdf_covers:
            try:
                from chaptr.pdf import CoverError, merge_covers
            except ImportError as error:
                raise BuildError("PDF covers require pypdf. Install chaptr's pdf extra.") from error
            try:
                document = merge_covers(document, pdf_covers)
            except CoverError as error:
                raise BuildError(str(error)) from error
        output.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(document)
    else:
        output.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    return destination


def init_project(directory: Path) -> Path:
    root = directory.resolve()
    starter_files = {
        resource.name: resource.read_text(encoding="utf-8")
        for resource in files("chaptr_docs").iterdir()
        if resource.is_file() and Path(resource.name).suffix in {".md", ".yaml", ".css"}
    }
    starter_files[".gitignore"] = "build/\n"
    if root.exists() and not root.is_dir():
        raise BuildError(f"Project directory is not a directory: {root}")
    conflicts = [
        name for name in starter_files
        if (root / name).exists() or (root / name).is_symlink()
    ]
    if conflicts:
        raise BuildError("Refusing to overwrite existing project files: " + ", ".join(conflicts))
    root.mkdir(parents=True, exist_ok=True)
    for name, content in starter_files.items():
        with (root / name).open("x", encoding="utf-8") as destination:
            destination.write(content)
    return root / "document.yaml"


def run_theme_command(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    action = args.themes_action
    if action == "list":
        themes = theme_manager.load_catalog()
        if not themes:
            print("No community themes are currently available.")
        for theme in themes:
            print(f"{theme.theme_id} ({theme.version}) - {theme.description}")
        return 0
    if action == "info":
        theme = theme_manager.get_theme(args.theme_id)
        print(f"{theme.name} ({theme.theme_id})")
        print(f"Version: {theme.version}")
        print(f"Description: {theme.description}")
        print(f"License: {theme.license}")
        print(f"Requires Chaptr: {theme.min_chaptr_version} or newer")
        return 0
    if action == "add":
        theme = theme_manager.add_theme(project_root, args.theme_id)
        print(f"Installed {theme.theme_id} {theme.version} in {project_root / 'themes'}")
        print(f"Set 'theme: {theme.theme_id}' in document.yaml to use it.")
        return 0
    if action == "check":
        updates = theme_manager.check_updates(project_root)
        if not updates:
            print("No Chaptr-managed themes are installed in this project.")
        for item in updates:
            if item.status == "update":
                print(
                    f"{item.theme_id}: {item.installed_version} -> {item.available_version}; "
                    f"run 'chaptr themes update {item.theme_id}'."
                )
            elif item.status == "unlisted":
                print(f"{item.theme_id} {item.installed_version}: no longer in the catalog.")
            elif item.status == "local-newer":
                print(f"{item.theme_id} {item.installed_version}: newer than the catalog entry.")
            else:
                print(f"{item.theme_id} {item.installed_version}: up to date.")
        return 0
    if action == "update":
        installed_version = theme_manager.installed_theme_version(project_root, args.theme_id)
        theme = theme_manager.update_theme(project_root, args.theme_id)
        if installed_version == theme.version:
            print(f"{theme.theme_id} is already up to date ({theme.version}).")
        else:
            print(f"Updated {theme.theme_id} from {installed_version} to {theme.version}.")
            print("The downloaded theme files were replaced; project stylesheet overrides are unchanged.")
        return 0
    raise BuildError(f"Unknown theme command: {action}")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="chaptr",
        description="Build independent Markdown document projects with variables and CSS themes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  chaptr init my-document\n"
            "  chaptr build --format pdf\n"
            "  chaptr build --config path/to/document.yaml\n"
            "  chaptr build --help\n\n"
            "  chaptr themes list\n"
            "  chaptr themes add roleplaying\n\n"
            "Run 'chaptr help' for the full usage manual."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    themes = commands.add_parser("themes", help="List, install and update community themes.")
    theme_commands = themes.add_subparsers(dest="themes_action", required=True)
    theme_commands.add_parser("list", help="List available community themes.")
    theme_info = theme_commands.add_parser("info", help="Show details for a community theme.")
    theme_info.add_argument("theme_id", metavar="THEME")
    theme_add = theme_commands.add_parser("add", help="Install a community theme in this project.")
    theme_add.add_argument("theme_id", metavar="THEME")
    theme_commands.add_parser("check", help="Check installed community themes for updates.")
    theme_update = theme_commands.add_parser("update", help="Update a managed community theme.")
    theme_update.add_argument("theme_id", metavar="THEME")
    initializer = commands.add_parser(
        "init",
        help="Create an editable project containing chaptr's documentation.",
        description="Copy chaptr's documentation, configuration, stylesheet and a build-output ignore rule.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  chaptr init\n"
            "  chaptr init my-document\n\n"
            "Existing starter files are never overwritten. Read or edit the\n"
            "documentation sections, then run 'chaptr build' from the project directory.\n"
            "Initialization does not require PDF dependencies."
        ),
    )
    initializer.add_argument(
        "directory", nargs="?", type=Path, default=Path("."), metavar="DIRECTORY",
        help="Project directory to create or use (default: current directory).",
    )
    command = commands.add_parser(
        "build",
        help="Build ordered chapters from a project configuration.",
        description="Combine configured Markdown chapters and write one document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  chaptr build\n"
            "  chaptr build --format pdf\n"
            "  chaptr build --config path/to/document.yaml --format markdown\n"
            "  chaptr build --theme vintage\n\n"
            "Project paths are relative to the configuration file. Output defaults\n"
            "to build/document.<extension> within that project; existing output\n"
            "of the same format is replaced. PDF requires WeasyPrint and its\n"
            "native libraries. Run 'chaptr help' for configuration and theme details."
        ),
    )
    command.add_argument(
        "--config", type=Path, default=Path("document.yaml"), metavar="PATH",
        help="YAML project configuration (default: document.yaml in the current directory).",
    )
    command.add_argument(
        "--format", choices=["markdown", "html", "pdf"], default="html",
        help="Output format (default: html); PDF requires optional renderer dependencies.",
    )
    command.add_argument(
        "--theme", metavar="NAME",
        help="Override the configured CSS theme for HTML/PDF; ignored for Markdown.",
    )
    commands.add_parser("help", help="Print the full usage manual.")
    args = parser.parse_args()
    if args.command == "help":
        print(files("chaptr").joinpath("manual.txt").read_text(encoding="utf-8"), end="")
        return 0
    try:
        if args.command == "themes":
            return run_theme_command(args)
        if args.command == "init":
            config_path = init_project(args.directory)
            print(f"Initialized project at {config_path.parent}")
            print("Start with README.md, then edit document.yaml and the Markdown sections.")
            print(f'Build with: chaptr build --config "{config_path.as_posix()}"')
            return 0
        destination = build(args.config, args.format, args.theme)
    except (BuildError, theme_manager.ThemeError, OSError, yaml.YAMLError) as error:
        print(f"chaptr: {error}", file=sys.stderr)
        return 1
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
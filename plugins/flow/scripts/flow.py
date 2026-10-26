#!/usr/bin/env python3
"""Flow command line. Standard library only.

flow.py build spec.json [-o dir]           place, check and draw a flowchart spec (HTML and draw.io)
flow.py split spec.json [-o dir]           split an ER spec by domain: an overview and one page each
flow.py check scene.json                   check a scene
flow.py render scene.json [-o out.html]    draw a scene as HTML
flow.py import file.drawio [-o dir]        read a draw.io file into a scene (HTML and draw.io)
flow.py edit file.drawio ops.json [-o out]  change a draw.io file: move, rename, recolour, delete
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flowlib import (
    build,
    check,
    edit_drawio,
    er_split,
    icon_check,
    import_drawio,
    overrides,
    render_drawio,
    render_html,
    scene,
    spec,
)

EXIT_OK = 0
EXIT_INVALID_INPUT = 1
EXIT_ERRORS_FOUND = 2


def load_local_icons(directory: Path) -> int | None:
    """Load the custom icons next to an input file, printing the problems if there are any.

    Args:
        directory: The folder of the spec or scene file.

    Returns:
        None when the icons loaded (or there are none), else the exit code to stop with.
    """
    try:
        icon_check.use_local_icons(directory)
    except spec.SpecError as error:
        print(
            f"the icons in {directory / icon_check.LOCAL_ICONS_FILE} are not valid:\n{error}",
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT
    return None


def run_render(arguments: argparse.Namespace) -> int:
    """Draw a scene file as an HTML file.

    Args:
        arguments: The parsed command line; ``scene`` is the input path and ``output`` the
            optional output path (default: the input path with an ``.html`` suffix).

    Returns:
        The exit code: 0 when the file was written, 1 when the scene is not valid.
    """
    failed = load_local_icons(Path(arguments.scene).resolve().parent)
    if failed is not None:
        return failed
    try:
        parsed = scene.load(arguments.scene)
    except scene.SceneError as error:
        print(f"{arguments.scene} is not a valid scene:\n{error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    output_path = Path(arguments.output or Path(arguments.scene).with_suffix(".html"))
    output_path.write_text(render_html.render(parsed), encoding="utf-8")
    print(f"wrote {output_path}")
    return EXIT_OK


def run_build(arguments: argparse.Namespace) -> int:
    """Place, check and draw a flowchart spec.

    Args:
        arguments: The parsed command line; ``spec`` is the input path and ``output`` the
            optional output folder (default: the folder of the spec).

    Returns:
        0 when the files were written and the checks found no error, 2 when they found at
        least one error (the files are still written), 1 when the spec is not valid.
    """
    spec_path = Path(arguments.spec)
    failed = load_local_icons(spec_path.resolve().parent)
    if failed is not None:
        return failed
    try:
        result = build.build(spec_path, Path(arguments.output or spec_path.parent))
    except spec.SpecError as error:
        print(f"{spec_path} is not a valid spec:\n{error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except overrides.OverridesError as error:
        print(f"the overrides next to {spec_path} are not valid:\n{error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    print(f"wrote {result.scene_path}\nwrote {result.html_path}\nwrote {result.drawio_path}")
    print(check.format_report(result.findings))
    has_errors = any(finding.severity is check.Severity.ERROR for finding in result.findings)
    return EXIT_ERRORS_FOUND if has_errors else EXIT_OK


def run_split(arguments: argparse.Namespace) -> int:
    """Split an ER spec by domain and build the overview and every domain page.

    Args:
        arguments: The parsed command line; ``spec`` is the ER spec and ``output`` the optional
            output folder (default: the folder of the spec).

    Returns:
        0 when every page was written and the checks found no error, 2 when they found at least
        one error (the files are still written), 1 when the spec cannot be split.
    """
    spec_path = Path(arguments.spec)
    out_dir = Path(arguments.output or spec_path.parent)
    try:
        pages = er_split.split_by_domain(json.loads(spec_path.read_text(encoding="utf-8")))
    except er_split.SplitError as error:
        print(f"{spec_path} cannot be split: {error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    out_dir.mkdir(parents=True, exist_ok=True)
    exit_code = EXIT_OK
    for name, page in pages.items():
        path = out_dir / f"{build.output_stem(spec_path)}-{name}{build.SPEC_SUFFIX}"
        path.write_text(json.dumps(page, indent=build.JSON_INDENT) + "\n", encoding="utf-8")
        try:
            result = build.build(path, out_dir)
        except spec.SpecError as error:
            print(f"{path} is not a valid spec:\n{error}", file=sys.stderr)
            return EXIT_INVALID_INPUT
        print(f"wrote {result.html_path}\nwrote {result.drawio_path}")
        print(check.format_report(result.findings))
        if any(f.severity is check.Severity.ERROR for f in result.findings):
            exit_code = EXIT_ERRORS_FOUND
    return exit_code


def run_import(arguments: argparse.Namespace) -> int:
    """Read a draw.io file into a scene and write the scene, an HTML page and a clean draw.io file.

    Args:
        arguments: The parsed command line; ``drawio`` is the input path and ``output`` the
            optional output folder (default: the folder of the input).

    Returns:
        0 when the files were written and the checks found no error, 2 when they found at
        least one error (the files are still written), 1 when the file cannot be read.
    """
    source = Path(arguments.drawio)
    try:
        result = import_drawio.convert(source)
    except spec.SpecError as error:
        print(f"{source} cannot be imported:\n{error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    out_dir = Path(arguments.output or source.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    paths = [out_dir / f"{stem}{build.SCENE_SUFFIX}", out_dir / f"{stem}{build.HTML_SUFFIX}"]
    paths.append(out_dir / f"{stem}.imported{build.DRAWIO_SUFFIX}")
    paths[0].write_text(scene.dumps(result.scene, build.JSON_INDENT) + "\n", encoding="utf-8")
    paths[1].write_text(render_html.render(result.scene), encoding="utf-8")
    paths[2].write_text(render_drawio.render(result.scene), encoding="utf-8")
    print("\n".join(f"wrote {path}" for path in paths))
    print("\n".join(f"note: {note}" for note in result.notes))
    findings = check.check_scene(result.scene)
    print(check.format_report(findings))
    has_errors = any(finding.severity is check.Severity.ERROR for finding in findings)
    return EXIT_ERRORS_FOUND if has_errors else EXIT_OK


def run_edit(arguments: argparse.Namespace) -> int:
    """Apply a list of operations to a draw.io file and write the result.

    Args:
        arguments: The parsed command line; ``drawio`` is the file, ``operations`` the JSON
            file of operations, ``output`` the optional output path (default: the file with
            ``.edited`` before the suffix) and ``in_place`` overwrites the file after keeping a
            ``.bak`` copy.

    Returns:
        0 when the file was written, 1 when the file or the operations are not valid.
    """
    source = Path(arguments.drawio)
    try:
        operations = json.loads(Path(arguments.operations).read_text(encoding="utf-8"))
        model, notes = edit_drawio.apply_operations(source, operations)
    except (OSError, json.JSONDecodeError) as error:
        print(f"cannot read the operations: {error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except spec.SpecError as error:
        print(f"the operations cannot be applied to {source}:\n{error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    if arguments.in_place:
        backup = source.with_name(source.name + ".bak")
        shutil.copyfile(source, backup)
        print(f"kept {backup}")
        destination = source
    else:
        destination = Path(arguments.output or source.with_suffix(".edited.drawio"))
    edit_drawio.write_edited(source, model, destination)
    print(f"wrote {destination}")
    print("\n".join(f"note: {note}" for note in dict.fromkeys(notes)))
    return EXIT_OK


def run_check(arguments: argparse.Namespace) -> int:
    """Check a scene file and print what is wrong.

    Args:
        arguments: The parsed command line; ``scene`` is the input path.

    Returns:
        0 when there is no error, 2 when there is at least one, 1 when the scene is not valid.
    """
    failed = load_local_icons(Path(arguments.scene).resolve().parent)
    if failed is not None:
        return failed
    try:
        parsed = scene.load(arguments.scene)
    except scene.SceneError as error:
        print(f"{arguments.scene} is not a valid scene:\n{error}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    findings = check.check_scene(parsed)
    print(check.format_report(findings))
    has_errors = any(finding.severity is check.Severity.ERROR for finding in findings)
    return EXIT_ERRORS_FOUND if has_errors else EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser, with one sub-command per action."""
    parser = argparse.ArgumentParser(prog="flow.py", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    build_command = commands.add_parser(
        "build", help="place, check and draw a flowchart spec (HTML and draw.io)"
    )
    build_command.add_argument("spec")
    build_command.add_argument("-o", "--output")
    build_command.set_defaults(run=run_build)
    split_command = commands.add_parser(
        "split", help="split an ER spec by domain into an overview and one page per domain"
    )
    split_command.add_argument("spec")
    split_command.add_argument("-o", "--output")
    split_command.set_defaults(run=run_split)
    check_command = commands.add_parser("check", help="check a scene")
    check_command.add_argument("scene")
    check_command.set_defaults(run=run_check)
    render = commands.add_parser("render", help="draw a scene as HTML")
    render.add_argument("scene")
    render.add_argument("-o", "--output")
    render.set_defaults(run=run_render)
    import_command = commands.add_parser("import", help="read a draw.io file into a scene")
    import_command.add_argument("drawio")
    import_command.add_argument("-o", "--output")
    import_command.set_defaults(run=run_import)
    edit_command = commands.add_parser(
        "edit", help="change a draw.io file with a list of operations"
    )
    edit_command.add_argument("drawio")
    edit_command.add_argument("operations")
    edit_command.add_argument("-o", "--output")
    edit_command.add_argument("--in-place", action="store_true")
    edit_command.set_defaults(run=run_edit)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line.

    Args:
        argv: The arguments after the program name; ``sys.argv`` is used when None.

    Returns:
        The exit code of the chosen command.
    """
    arguments = build_parser().parse_args(argv)
    return arguments.run(arguments)


if __name__ == "__main__":
    sys.exit(main())

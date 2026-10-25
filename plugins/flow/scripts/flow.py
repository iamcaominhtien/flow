#!/usr/bin/env python3
"""Flow command line. Standard library only.

flow.py build spec.json [-o dir]           place, check and draw a flowchart spec (HTML and draw.io)
flow.py check scene.json                   check a scene
flow.py render scene.json [-o out.html]    draw a scene as HTML
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flowlib import build, check, overrides, render_html, scene, spec

EXIT_OK = 0
EXIT_INVALID_INPUT = 1
EXIT_ERRORS_FOUND = 2


def run_render(arguments: argparse.Namespace) -> int:
    """Draw a scene file as an HTML file.

    Args:
        arguments: The parsed command line; ``scene`` is the input path and ``output`` the
            optional output path (default: the input path with an ``.html`` suffix).

    Returns:
        The exit code: 0 when the file was written, 1 when the scene is not valid.
    """
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


def run_check(arguments: argparse.Namespace) -> int:
    """Check a scene file and print what is wrong.

    Args:
        arguments: The parsed command line; ``scene`` is the input path.

    Returns:
        0 when there is no error, 2 when there is at least one, 1 when the scene is not valid.
    """
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
    check_command = commands.add_parser("check", help="check a scene")
    check_command.add_argument("scene")
    check_command.set_defaults(run=run_check)
    render = commands.add_parser("render", help="draw a scene as HTML")
    render.add_argument("scene")
    render.add_argument("-o", "--output")
    render.set_defaults(run=run_render)
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

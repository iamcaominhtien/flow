#!/usr/bin/env python3
"""Flow command line. Standard library only.

flow.py render scene.json [-o out.html]    draw a scene as HTML
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flowlib import render_html, scene

EXIT_OK = 0
EXIT_INVALID_SCENE = 1


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
        return EXIT_INVALID_SCENE
    output_path = Path(arguments.output or Path(arguments.scene).with_suffix(".html"))
    output_path.write_text(render_html.render(parsed), encoding="utf-8")
    print(f"wrote {output_path}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser, with one sub-command per action."""
    parser = argparse.ArgumentParser(prog="flow.py", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
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

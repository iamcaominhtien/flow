#!/usr/bin/env python3
"""Flow command line. Standard library only.

flow.py render scene.json [-o out.html]    draw a scene as HTML
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flowlib import render_html, scene


def cmd_render(args):
    try:
        data = scene.load(args.scene)
    except scene.SceneError as err:
        print(f"{args.scene} is not a valid scene:\n{err}", file=sys.stderr)
        return 1
    out = Path(args.output) if args.output else Path(args.scene).with_suffix(".html")
    out.write_text(render_html.render(data), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="flow.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("render", help="draw a scene as HTML")
    r.add_argument("scene")
    r.add_argument("-o", "--output")
    r.set_defaults(run=cmd_render)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())

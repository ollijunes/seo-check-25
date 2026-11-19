"""Command line interface."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .checks import FIX, NOT_CHECKED, REVIEW, run
from .site import load

EXIT_OK = 0
EXIT_FIX = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seo-check",
        description="Run the machine-checkable part of the 25-point SEO check on a built site.",
    )
    parser.add_argument("--version", action="version", version=f"seo-check {__version__}")
    parser.add_argument("folder", help="the build folder, for example dist")
    parser.add_argument(
        "--site", default="", help="the site's address, to treat its links as internal"
    )
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("--all", action="store_true", help="show every line of evidence")
    parser.add_argument(
        "--strict", action="store_true", help="exit with code 1 when a point is FIX"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.folder)
    if not root.is_dir():
        print(f"seo-check: not a folder: {root}", file=sys.stderr)
        return EXIT_ERROR
    site = load(root, args.site)
    if not site.pages:
        print(f"seo-check: no .html files under {root}", file=sys.stderr)
        return EXIT_ERROR
    results = run(site)
    counts = {
        status: sum(result.status == status for result in results)
        for status in (FIX, REVIEW, NOT_CHECKED)
    }

    if args.json:
        payload = {
            "pages": len(site.pages),
            "summary": {
                "fix": counts[FIX],
                "review": counts[REVIEW],
                "not_checked": counts[NOT_CHECKED],
            },
            "results": [asdict(result) for result in results],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        limit = None if args.all else 5
        for result in results:
            print(f"{result.number:>2}  {result.status:<11}  {result.title}: {result.summary}")
            shown = result.evidence if limit is None else result.evidence[:limit]
            for line in shown:
                print(f"      {line}")
            if len(result.evidence) > len(shown):
                print(f"      and {len(result.evidence) - len(shown)} more (--all shows them)")
        print(
            f"\n{len(site.pages)} pages. {counts[FIX]} to fix, {counts[REVIEW]} to review, "
            f"{counts[NOT_CHECKED]} not checked here: "
            "those need the live site, the owner or a reader."
        )
    return EXIT_FIX if args.strict and counts[FIX] else EXIT_OK

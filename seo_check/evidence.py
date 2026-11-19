"""Read one page's Firecrawl Local and SEOmator JSON reports from disk."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit


def page_key(url):
    if not isinstance(url, str):
        raise ValueError("missing page URL")
    address = urlsplit(url)
    if address.scheme not in {"http", "https"} or not address.hostname:
        raise ValueError("expected an HTTP or HTTPS page URL")
    if address.username is not None:
        raise ValueError("credentials are not supported in page URLs")
    port = address.port if address.port is not None else (443 if address.scheme == "https" else 80)
    return address.scheme, address.hostname, port, address.path or "/", address.query


def read_report(path):
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("expected a single-page JSON object")
    return report


def firecrawl(report, page):
    if report.get("success") is not True:
        raise ValueError("Firecrawl reported a failed scrape")
    data = report["data"]
    meta = data["metadata"]
    if page_key(meta["sourceURL"]) != page:
        raise ValueError("Firecrawl source URL differs from the requested page")
    status = meta["statusCode"]
    if (
        type(status) is not int
        or not 200 <= status < 300
        or data.get("blocked")
        or meta.get("blocked")
    ):
        raise ValueError("Firecrawl did not retrieve a usable page")
    content = data["markdown"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Firecrawl returned no Markdown")
    return {
        "source_url": meta["sourceURL"],
        "final_url": meta.get("url"),
        "status": status,
        "title": meta.get("title"),
        "markdown_characters": len(content),
    }


def seomator(report, page):
    if (
        page_key(report["url"]) != page
        or type(report.get("crawledPages")) is not int
        or report["crawledPages"] != 1
        or report.get("run", {}).get("crawl")
    ):
        raise ValueError("expected a single-page SEOmator audit of the requested URL")
    score = report["overallScore"]
    if type(score) not in {int, float} or not 0 <= score <= 100:
        raise ValueError("invalid SEOmator score")
    categories = []
    for category in report["categoryResults"]:
        counts = {
            key: category[key]
            for key in ("passCount", "warnCount", "failCount", "notMeasuredCount")
        }
        counts["advisoryCount"] = category.get("advisoryCount", 0)
        if any(type(count) is not int or count < 0 for count in counts.values()):
            raise ValueError("invalid SEOmator rule count")
        categories.append({"id": category["categoryId"], **counts})
    if not categories:
        raise ValueError("SEOmator returned no categories")
    return {"score": score, "categories": categories}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="the audited page URL")
    parser.add_argument("--firecrawl", type=Path, help="a Firecrawl Local scrape JSON file")
    parser.add_argument("--seomator", type=Path, help="a SEOmator 8 single-page audit JSON file")
    args = parser.parse_args(argv)
    if not (args.firecrawl or args.seomator):
        parser.error("supply --firecrawl, --seomator, or both")
    try:
        page = page_key(args.url)
        evidence = {"url": args.url}
        if args.firecrawl:
            evidence["firecrawl"] = firecrawl(read_report(args.firecrawl), page)
        if args.seomator:
            evidence["seomator"] = seomator(read_report(args.seomator), page)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"seo-check-evidence: {error}", file=sys.stderr)
        return 2
    print(json.dumps(evidence, indent=2))
    return 0

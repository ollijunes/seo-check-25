"""The 25 points. Each returns a Result; points that need the live site say so."""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .site import Site

OK = "OK"
FIX = "FIX"
REVIEW = "REVIEW"
NOT_APPLICABLE = "N/A"
NOT_CHECKED = "NOT CHECKED"

GOOGLEBOT_FILE_LIMIT = 2_000_000
LARGE_IMAGE = 300_000
LEGACY_IMAGE = re.compile(r"\.(jpe?g|png|gif)$", re.IGNORECASE)

SEARCH_BOTS = ("Googlebot", "Bingbot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot")
TRAINING_BOTS = ("GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot")


@dataclass
class Result:
    number: int
    title: str
    status: str
    summary: str
    evidence: list[str] = field(default_factory=list)


def run(site: Site) -> list[Result]:
    checks = (
        rendered_html,
        sitemap,
        search_console,
        robots_googlebot,
        noindex,
        redirects,
        broken_links,
        canonical,
        meta_description,
        one_h1,
        faq,
        breadcrumbs,
        orphans,
        alt_text,
        images,
        layout_shift,
        load_time,
        ai_slop,
        author,
        backlinks,
        spam_policies,
        ai_bots,
        snippet_controls,
        main_content,
        bing,
    )
    return [check(site) for check in checks]


def _manual(number: int, title: str, why: str) -> Result:
    return Result(number, title, NOT_CHECKED, why)


def _indexable(site: Site):
    return [page for page in site.pages if page.indexable]


def rendered_html(site: Site) -> Result:
    title = "Content is in the HTML without JavaScript"
    evidence = []
    for page in _indexable(site):
        if page.h1 == 0 and page.words < 50:
            evidence.append(f"{page.file}: no h1 and {page.words} words in the raw HTML")
    for name, size in site.files.items():
        if name.lower().endswith((".html", ".css", ".js", ".mjs")) and size > GOOGLEBOT_FILE_LIMIT:
            evidence.append(f"{name}: {size / 1_000_000:.1f} MB, over Googlebot's 2 MB per file")
    if evidence:
        return Result(1, title, FIX, f"{len(evidence)} pages or files", evidence)
    return Result(1, title, OK, "every indexable page has text in the raw HTML; no file over 2 MB")


def sitemap(site: Site) -> Result:
    title = "Sitemap"
    if site.sitemap_urls is None:
        return Result(2, title, FIX, "no sitemap*.xml in the build folder")
    listed = set()
    evidence = []
    for url in site.sitemap_urls:
        path = site.local(urlsplit(url).path)
        if path is None:
            evidence.append(f"{url}: in the sitemap, outside the site's base path")
        else:
            listed.add(path.rstrip("/") or "/")
    for path in sorted(listed):
        page = site.page_for(path)
        if page is None:
            evidence.append(f"{path}: in the sitemap, no such page")
        elif not page.indexable:
            evidence.append(f"{path}: in the sitemap but noindex or a redirect")
    for page in _indexable(site):
        if (page.url_path.rstrip("/") or "/") not in listed:
            evidence.append(f"{page.url_path}: indexable but not in the sitemap")
    if evidence:
        return Result(2, title, FIX, f"{len(evidence)} mismatches", evidence)
    return Result(2, title, OK, f"{len(listed)} URLs, all indexable pages listed")


def search_console(site: Site) -> Result:
    return _manual(
        3, "Sitemap submitted to Search Console", "needs the owner's Search Console; see the skill"
    )


def _robots_groups(text: str) -> list[tuple[list[str], list[tuple[str, str]]]]:
    groups: list[tuple[list[str], list[tuple[str, str]]]] = []
    agents: list[str] = []
    rules: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if rules:
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(value.lower())
        elif key in ("allow", "disallow"):
            rules.append((key, value))
    if agents:
        groups.append((agents, rules))
    return groups


def bot_access(text: str, bot: str) -> str:
    """allowed, blocked, partly blocked or not mentioned, by the bot's own group or `*`."""
    groups = _robots_groups(text)
    own = [rules for agents, rules in groups if bot.lower() in agents]
    chosen = own or [rules for agents, rules in groups if "*" in agents]
    if not chosen:
        return "not mentioned"
    rules = [rule for group in chosen for rule in group]
    disallows = [value for key, value in rules if key == "disallow" and value]
    allows_root = any(key == "allow" and value in ("/", "/*") for key, value in rules)
    if any(value in ("/", "/*") for value in disallows) and not allows_root:
        state = "blocked"
    elif disallows:
        state = "partly blocked"
    else:
        state = "allowed"
    return state if own else f"{state} (by the * group)"


def robots_googlebot(site: Site) -> Result:
    title = "robots.txt lets Googlebot in"
    if site.robots is None:
        return Result(4, title, FIX, "no robots.txt in the build folder")
    evidence = []
    access = bot_access(site.robots, "Googlebot")
    if access.startswith("blocked"):
        evidence.append(f"Googlebot is {access}")
    if not re.search(r"^\s*sitemap\s*:", site.robots, re.IGNORECASE | re.MULTILINE):
        evidence.append("no Sitemap: line")
    if evidence:
        return Result(4, title, FIX, "; ".join(evidence), evidence)
    return Result(4, title, OK, f"Googlebot {access}; Sitemap line present")


def noindex(site: Site) -> Result:
    title = "noindex only where intended"
    pages = [page for page in site.pages if page.noindex]
    if not pages:
        return Result(5, title, OK, "no noindex pages")
    evidence = [f"{page.url_path}: {page.robots}" for page in pages]
    if any(page.url_path == "/" for page in pages):
        return Result(5, title, FIX, "the home page is noindex", evidence)
    return Result(
        5, title, REVIEW, f"{len(pages)} noindex pages; confirm each is intended", evidence
    )


def redirects(site: Site) -> Result:
    return _manual(6, "No redirect chains", "needs the live site; see the skill for the curl line")


def broken_links(site: Site) -> Result:
    title = "No broken internal links"
    evidence = []
    for page in site.pages:
        for href in page.links:
            target = site.resolve(href, page)
            if target is not None and not site.exists(target):
                evidence.append(f"{page.file}: {href}")
    if evidence:
        return Result(7, title, FIX, f"{len(evidence)} links to pages that do not exist", evidence)
    return Result(7, title, OK, "every internal link points to a file in the build")


def canonical(site: Site) -> Result:
    title = "One canonical link per page"
    broken, elsewhere = [], []
    for page in _indexable(site):
        if len(page.canonicals) != 1:
            broken.append(f"{page.file}: {len(page.canonicals)} canonical links")
            continue
        parts = urlsplit(page.canonicals[0])
        if parts.scheme != "https" or not parts.netloc:
            broken.append(f"{page.file}: not an absolute https address: {page.canonicals[0]}")
        elif site.host and parts.netloc.lower().removeprefix("www.") != site.host:
            broken.append(f"{page.file}: other domain: {parts.netloc}")
        elif ((site.local(parts.path) or parts.path).rstrip("/") or "/") != (
            page.url_path.rstrip("/") or "/"
        ):
            elsewhere.append(f"{page.file}: points to {parts.path}")
    if broken:
        return Result(8, title, FIX, f"{len(broken)} pages", broken + elsewhere)
    if elsewhere:
        return Result(8, title, REVIEW, f"{len(elsewhere)} pages point to another page", elsewhere)
    return Result(8, title, OK, "one absolute, self-referencing canonical on every indexable page")


def meta_description(site: Site) -> Result:
    title = "A meta description on every page"
    pages = _indexable(site)
    evidence = [f"{page.file}: missing" for page in pages if not any(page.descriptions)]
    seen = defaultdict(list)
    for page in pages:
        for text in page.descriptions[:1]:
            if text:
                seen[text].append(page.file)
    for files in seen.values():
        if len(files) > 1:
            evidence.append(f"same description on {len(files)} pages: {', '.join(files[:4])}")
    if evidence:
        return Result(9, title, FIX, f"{len(evidence)} findings", evidence)
    lengths = [len(page.descriptions[0]) for page in pages]
    odd = sum(1 for length in lengths if not 70 <= length <= 160)
    note = f"; {odd} outside 70–160 characters" if odd else ""
    return Result(9, title, OK, f"present and unique on {len(pages)} pages{note}")


def one_h1(site: Site) -> Result:
    title = "One h1 per page"
    evidence = [f"{page.file}: {page.h1} h1 elements" for page in _indexable(site) if page.h1 != 1]
    if evidence:
        return Result(10, title, FIX, f"{len(evidence)} pages", evidence)
    return Result(10, title, OK, "exactly one on every indexable page")


def faq(site: Site) -> Result:
    title = "FAQ content is visible text"
    pages = [page.file for page in site.pages if "FAQPage" in page.schema_types]
    if not pages:
        return Result(11, title, NOT_APPLICABLE, "no FAQPage markup found")
    return Result(
        11,
        title,
        REVIEW,
        f"FAQPage markup on {len(pages)} pages: check that it matches the visible text",
        pages,
    )


def breadcrumbs(site: Site) -> Result:
    title = "Breadcrumbs on deeper pages"
    deep = [page for page in _indexable(site) if page.depth >= 2]
    if not deep:
        return Result(12, title, NOT_APPLICABLE, "no pages below the first level")
    evidence = [
        f"{page.file}: no BreadcrumbList"
        for page in deep
        if "BreadcrumbList" not in page.schema_types
    ]
    if evidence:
        return Result(12, title, FIX, f"{len(evidence)} of {len(deep)} deeper pages", evidence)
    return Result(12, title, OK, f"BreadcrumbList on all {len(deep)} deeper pages")


def orphans(site: Site) -> Result:
    title = "No orphan pages"
    inbound: Counter[str] = Counter()
    for page in site.pages:
        targets = set()
        for href in page.links:
            target = site.resolve(href, page)
            if target is not None:
                targets.add(target.rstrip("/") or "/")
        targets.discard(page.url_path.rstrip("/") or "/")
        inbound.update(targets)
    evidence = []
    for page in _indexable(site):
        key = page.url_path.rstrip("/") or "/"
        if key != "/" and inbound[key] == 0:
            evidence.append(f"{page.url_path}: no internal link points here")
    if evidence:
        return Result(13, title, FIX, f"{len(evidence)} orphan pages", evidence)
    single = sum(1 for page in _indexable(site) if inbound[page.url_path.rstrip("/") or "/"] == 1)
    note = f"; {single} pages have only one" if single else ""
    return Result(13, title, OK, f"every page has an internal link pointing to it{note}")


def alt_text(site: Site) -> Result:
    title = "Alt text on images"
    evidence = []
    decorative = 0
    for page in site.pages:
        for image in page.images:
            if not image.has_alt:
                evidence.append(f"{page.file}: {image.src or '(no src)'}")
            elif not image.alt.strip():
                decorative += 1
    if evidence:
        return Result(14, title, FIX, f"{len(evidence)} images without an alt attribute", evidence)
    note = f'; {decorative} with alt="" (fine for decoration only)' if decorative else ""
    return Result(14, title, OK, f"every image has an alt attribute{note}")


def images(site: Site) -> Result:
    title = "Modern image formats and sizes"
    heavy = [
        f"{name}: {size // 1000} kB"
        for name, size in site.files.items()
        if LEGACY_IMAGE.search(name) and size > LARGE_IMAGE
    ]
    unsized = [
        f"{page.file}: {image.src}"
        for page in site.pages
        for image in page.images
        if not image.has_size and not image.src.lower().endswith(".svg")
    ]
    if heavy:
        return Result(15, title, FIX, f"{len(heavy)} JPEG, PNG or GIF files over 300 kB", heavy)
    if unsized:
        return Result(15, title, REVIEW, f"{len(unsized)} images without width and height", unsized)
    return Result(15, title, OK, "no large legacy-format images; images carry width and height")


def layout_shift(site: Site) -> Result:
    return _manual(16, "CLS and INP", "needs field data (CrUX, PageSpeed Insights, Search Console)")


def load_time(site: Site) -> Result:
    return _manual(17, "LCP and time to first byte", "needs the live site and field data")


def ai_slop(site: Site) -> Result:
    return _manual(18, "No machine-sounding text", "needs reading; see the skill")


def author(site: Site) -> Result:
    title = "A real author"
    count = sum(1 for page in site.pages if "Person" in page.schema_types)
    if count:
        return Result(
            19, title, REVIEW, f"Person markup on {count} pages: check that the person is real"
        )
    return _manual(19, title, "no Person markup found; check the author page by reading")


def backlinks(site: Site) -> Result:
    return _manual(20, "Quality backlinks", "needs a backlink index and the owner")


def spam_policies(site: Site) -> Result:
    title = "Spam policies"
    pages = [page.file for page in site.pages if page.history_api]
    if pages:
        return Result(
            21,
            title,
            REVIEW,
            f"inline scripts on {len(pages)} pages call history.pushState or replaceState: "
            "rule out back-button hijacking; the other policies need reading",
            pages,
        )
    return _manual(21, title, "needs reading; no inline history manipulation found")


def ai_bots(site: Site) -> Result:
    title = "AI crawler access in robots.txt"
    if site.robots is None:
        return Result(22, title, REVIEW, "no robots.txt: every crawler is allowed by default")
    evidence = [f"search    {bot}: {bot_access(site.robots, bot)}" for bot in SEARCH_BOTS]
    evidence += [f"training  {bot}: {bot_access(site.robots, bot)}" for bot in TRAINING_BOTS]
    blocked = [bot for bot in SEARCH_BOTS if bot_access(site.robots, bot).startswith("blocked")]
    note = "a firewall or CDN can still block them: test the live site"
    if blocked:
        return Result(22, title, FIX, f"search crawlers blocked: {', '.join(blocked)}", evidence)
    return Result(22, title, OK, f"no search crawler is blocked; {note}", evidence)


def snippet_controls(site: Site) -> Result:
    title = "No accidental snippet limits"
    evidence = []
    pattern = re.compile(r"nosnippet|max-snippet\s*:\s*0\b|noarchive|unavailable_after")
    for page in _indexable(site):
        found = sorted(set(pattern.findall(page.robots)))
        if page.nosnippet_attributes:
            found.append(f"data-nosnippet ×{page.nosnippet_attributes}")
        if found:
            evidence.append(f"{page.file}: {', '.join(found)}")
    if evidence:
        return Result(23, title, REVIEW, f"{len(evidence)} pages limit snippets", evidence)
    return Result(23, title, OK, "no nosnippet, max-snippet:0, noarchive or data-nosnippet")


def main_content(site: Site) -> Result:
    return _manual(24, "Main content: effort, originality, skill, accuracy", "needs reading")


def bing(site: Site) -> Result:
    return _manual(25, "Bing index", "needs the owner's Bing Webmaster Tools")

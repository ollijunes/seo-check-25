"""Read a built site from disk: pages, robots.txt, sitemaps and asset sizes."""

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

MAX_HTML_BYTES = 20_000_000
HISTORY_API = re.compile(r"history\.(pushState|replaceState)\s*\(")
WORD = re.compile(r"[^\W\d_]{2,}")
VOID_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}


@dataclass
class Image:
    src: str
    has_alt: bool
    alt: str
    has_size: bool


@dataclass
class Page:
    file: str
    url_path: str
    size: int
    lang: str = ""
    title: str = ""
    h1: int = 0
    descriptions: list[str] = field(default_factory=list)
    canonicals: list[str] = field(default_factory=list)
    robots: str = ""
    refresh: bool = False
    links: list[str] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)
    schema_types: set[str] = field(default_factory=set)
    nosnippet_attributes: int = 0
    history_api: bool = False
    words: int = 0

    @property
    def noindex(self) -> bool:
        return "noindex" in self.robots

    @property
    def indexable(self) -> bool:
        return not self.noindex and not self.refresh and self.url_path not in ("/404", "/404/")

    @property
    def depth(self) -> int:
        return len([part for part in self.url_path.split("/") if part])


class _Reader(HTMLParser):
    def __init__(self, page: Page):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.stack: list[str] = []
        self.buffer: list[str] = []
        self.capture = ""
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        values = {name: (value or "") for name, value in attrs}
        page = self.page
        if tag in VOID_TEXT_TAGS:
            self.stack.append(tag)
        if "data-nosnippet" in values:
            page.nosnippet_attributes += 1
        if tag == "html":
            page.lang = values.get("lang", "").lower()
        elif tag == "body":
            self.in_body = True
        elif tag == "title" and not page.title:
            self._start("title")
        elif tag == "h1":
            page.h1 += 1
        elif tag == "meta":
            name = values.get("name", "").lower()
            content = values.get("content", "")
            if name == "description":
                page.descriptions.append(" ".join(content.split()))
            elif name in ("robots", "googlebot"):
                page.robots = f"{page.robots} {content.lower()}".strip()
            elif values.get("http-equiv", "").lower() == "refresh":
                page.refresh = True
        elif tag == "link":
            if "canonical" in values.get("rel", "").lower().split():
                page.canonicals.append(values.get("href", ""))
        elif tag == "a" and values.get("href"):
            page.links.append(values["href"].strip())
        elif tag == "img":
            page.images.append(
                Image(
                    src=values.get("src", ""),
                    has_alt="alt" in values,
                    alt=values.get("alt", ""),
                    has_size="width" in values and "height" in values,
                )
            )
        elif tag == "script":
            kind = values.get("type", "").lower()
            self._start("jsonld" if kind == "application/ld+json" else "script")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in VOID_TEXT_TAGS:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID_TEXT_TAGS and self.stack and self.stack[-1] == tag:
            self.stack.pop()
        if tag == "title" and self.capture == "title":
            self.page.title = " ".join("".join(self.buffer).split())
            self.capture = ""
        elif tag == "script" and self.capture in ("jsonld", "script"):
            text = "".join(self.buffer)
            if self.capture == "jsonld":
                self.page.schema_types |= _schema_types(text)
            elif HISTORY_API.search(text):
                self.page.history_api = True
            self.capture = ""

    def handle_data(self, data):
        if self.capture:
            self.buffer.append(data)
        elif self.in_body and not self.stack:
            self.page.words += len(WORD.findall(data))

    def _start(self, kind: str):
        self.capture = kind
        self.buffer = []


def _schema_types(text: str) -> set[str]:
    try:
        data = json.loads(text)
    except ValueError:
        return {"(invalid JSON-LD)"}
    found: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            kind = node.get("@type")
            for name in kind if isinstance(kind, list) else [kind]:
                if isinstance(name, str):
                    found.add(name)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return found


def url_path_of(file: str) -> str:
    """blog/post/index.html -> /blog/post/ and blog/post.html -> /blog/post"""
    if file == "index.html":
        return "/"
    if file.endswith("/index.html"):
        return "/" + file[: -len("index.html")]
    return "/" + file[: -len(".html")]


def read_page(root: Path, file: str) -> Page:
    data = (root / file).read_bytes()
    page = Page(file=file, url_path=url_path_of(file), size=len(data))
    reader = _Reader(page)
    reader.feed(data[:MAX_HTML_BYTES].decode("utf-8", errors="replace"))
    reader.close()
    return page


@dataclass
class Site:
    root: Path
    pages: list[Page]
    files: dict[str, int]
    robots: str | None
    sitemap_urls: list[str] | None
    host: str = ""
    base: str = ""

    def local(self, path: str) -> str | None:
        """A served path as a path inside the build folder; None when it is outside the base."""
        if not self.base:
            return path or "/"
        if path == self.base or path.startswith(self.base + "/"):
            return path[len(self.base) :] or "/"
        return None

    def page_for(self, url_path: str) -> Page | None:
        key = url_path.rstrip("/") or "/"
        return self._by_path.get(key)

    def __post_init__(self):
        self._by_path = {(page.url_path.rstrip("/") or "/"): page for page in self.pages}

    def resolve(self, href: str, page: Page) -> str | None:
        """The path inside the site an internal link points to, or None for other links."""
        parts = urlsplit(href)
        if parts.scheme and parts.scheme not in ("http", "https"):
            return None
        if parts.netloc:
            if not self.host or parts.netloc.lower().removeprefix("www.") != self.host:
                return None
        path = unquote(parts.path)
        if not path:
            return None
        if path.startswith("/"):
            path = self.local(path)
            if path is None:
                return None
        else:
            base = (
                page.url_path
                if page.url_path.endswith("/")
                else page.url_path.rsplit("/", 1)[0] + "/"
            )
            path = base + path
        segments: list[str] = []
        for segment in path.split("/"):
            if segment == "..":
                if segments:
                    segments.pop()
            elif segment not in ("", "."):
                segments.append(segment)
        return "/" + "/".join(segments) + ("/" if path.endswith("/") and segments else "")

    def exists(self, path: str) -> bool:
        bare = path.strip("/")
        if not bare:
            return "index.html" in self.files
        candidates = (bare, f"{bare}.html", f"{bare}/index.html")
        return any(candidate in self.files for candidate in candidates)


def load(root: Path, site_url: str = "") -> Site:
    files: dict[str, int] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        files[path.relative_to(root).as_posix()] = path.stat().st_size
    pages = [read_page(root, name) for name in files if name.lower().endswith(".html")]
    robots_file = root / "robots.txt"
    robots = (
        robots_file.read_text(encoding="utf-8", errors="replace") if robots_file.is_file() else None
    )
    parts = urlsplit(site_url) if site_url else None
    host = parts.netloc.lower().removeprefix("www.") if parts else ""
    # https://example.com/docs/ serves the build folder under /docs.
    base = parts.path.rstrip("/") if parts else ""
    return Site(root, pages, files, robots, _sitemap_urls(root, files), host, base)


def _sitemap_urls(root: Path, files: dict[str, int]) -> list[str] | None:
    names = [name for name in files if re.fullmatch(r"sitemap[^/]*\.xml", name)]
    if not names:
        return None
    urls: list[str] = []
    for name in names:
        text = (root / name).read_text(encoding="utf-8", errors="replace")
        if "<sitemapindex" in text:
            continue
        urls.extend(match.strip() for match in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", text))
    return urls

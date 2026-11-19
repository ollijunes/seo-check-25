import pytest

SITE = "https://example.com"

ROBOTS = """User-agent: *
Allow: /

User-agent: GPTBot
Disallow: /

Sitemap: https://example.com/sitemap-index.xml
"""


def html(
    path: str,
    *,
    title: str = "Rye bread",
    description: str | None = None,
    h1: str | None = "Rye bread",
    head: str = "",
    body: str = "",
    canonical: str | None = "",
    crumbs: bool = True,
) -> str:
    """A small page that passes every check. Tests break one thing at a time."""
    words = "Mix the flour and the water and wait for two days until the starter is sour. " * 5
    if description is None:
        description = (
            f"How to bake {title.lower()} at home with a two-day sour starter, "
            "explained step by step."
        )
    if canonical == "":
        canonical = f"{SITE}{path}"
    crumb = (
        '<script type="application/ld+json">{"@context":"https://schema.org",'
        '"@type":"BreadcrumbList","itemListElement":[]}</script>'
        if crumbs
        else ""
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<meta name="description" content="{description}">
{f'<link rel="canonical" href="{canonical}">' if canonical else ""}
{crumb}{head}</head>
<body><nav><a href="/">Home</a> <a href="/blog/">Blog</a> <a href="/about/">About</a></nav>
<main>{f"<h1>{h1}</h1>" if h1 else ""}<p>{words}</p>{body}</main></body></html>
"""


def sitemap(*paths: str) -> str:
    locs = "".join(f"<url><loc>{SITE}{path}</loc></url>" for path in paths)
    return f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'


class Build:
    def __init__(self, root):
        self.root = root

    def write(self, name: str, text: str | bytes):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")
        return self

    def good(self):
        """Home, a blog index, two posts and an about page, all linked and listed."""
        posts = '<a href="/blog/rye/">Rye</a> <a href="oats/">Oats</a>'
        self.write("index.html", html("/", title="Home", h1="Home", crumbs=False))
        self.write("about/index.html", html("/about/", title="About", h1="About", crumbs=False))
        self.write(
            "blog/index.html", html("/blog/", title="Blog", h1="Blog", body=posts, crumbs=False)
        )
        self.write("blog/rye/index.html", html("/blog/rye/", body='<a href="../oats/">Oats</a>'))
        self.write(
            "blog/oats/index.html",
            html(
                "/blog/oats/",
                title="Oat bread",
                h1="Oat bread",
                body='<img src="/img/loaf.webp" alt="A loaf" width="800" height="600">',
            ),
        )
        self.write("img/loaf.webp", b"x" * 1000)
        self.write("robots.txt", ROBOTS)
        self.write(
            "sitemap-index.xml", "<sitemapindex><sitemap><loc>x</loc></sitemap></sitemapindex>"
        )
        self.write("sitemap-0.xml", sitemap("/", "/about/", "/blog/", "/blog/rye/", "/blog/oats/"))
        return self


@pytest.fixture
def build(tmp_path):
    return Build(tmp_path)

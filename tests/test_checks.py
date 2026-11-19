from seo_check import checks
from seo_check.checks import FIX, NOT_APPLICABLE, NOT_CHECKED, OK, REVIEW, bot_access, run
from seo_check.site import load, url_path_of
from tests.conftest import ROBOTS, SITE, html, sitemap


def results(build, site=SITE):
    return {result.number: result for result in run(load(build.root, site))}


def test_a_clean_site_has_nothing_to_fix(build):
    found = results(build.good())
    assert len(found) == 25
    assert sorted(found) == list(range(1, 26))
    statuses = {number: result.status for number, result in found.items()}
    assert [number for number, status in statuses.items() if status == FIX] == []
    assert [number for number, status in statuses.items() if status == REVIEW] == []
    for number in (1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15, 22, 23):
        assert statuses[number] == OK, found[number]
    for number in (3, 6, 16, 17, 18, 19, 20, 21, 24, 25):
        assert statuses[number] == NOT_CHECKED, found[number]
    assert statuses[11] == NOT_APPLICABLE


def test_1_text_missing_from_raw_html_and_oversized_files(build):
    build.good().write("app/index.html", '<html><body><div id="root"></div></body></html>')
    build.write("assets/big.js", b"x" * 2_000_001)
    result = results(build)[1]
    assert result.status == FIX
    assert result.evidence == [
        "app/index.html: no h1 and 0 words in the raw HTML",
        "assets/big.js: 2.0 MB, over Googlebot's 2 MB per file",
    ]


def test_1_script_and_style_text_is_not_content(build):
    page = "<html><body><script>var a = 'many words here to count';</script>"
    page += "<style>.many { words: here }</style><svg><text>words in a drawing</text></svg>"
    page += "</body></html>"
    build.good().write("app/index.html", page)
    assert "0 words" in results(build)[1].evidence[0]


def test_2_sitemap_mismatches(build):
    build.good()
    build.write("blog/new/index.html", html("/blog/new/"))
    build.write(
        "thanks/index.html", html("/thanks/", head='<meta name="robots" content="noindex">')
    )
    build.write(
        "sitemap-0.xml",
        sitemap("/", "/about/", "/blog/", "/blog/rye/", "/blog/oats/", "/gone/", "/thanks/"),
    )
    result = results(build)[2]
    assert result.status == FIX
    assert result.evidence == [
        "/gone: in the sitemap, no such page",
        "/thanks: in the sitemap but noindex or a redirect",
        "/blog/new/: indexable but not in the sitemap",
    ]


def test_2_no_sitemap(build):
    build.good()
    (build.root / "sitemap-0.xml").unlink()
    (build.root / "sitemap-index.xml").unlink()
    assert results(build)[2].summary == "no sitemap*.xml in the build folder"


def test_4_robots(build):
    build.good().write("robots.txt", "User-agent: *\nDisallow: /\n")
    result = results(build)[4]
    assert result.status == FIX
    assert result.evidence == ["Googlebot is blocked (by the * group)", "no Sitemap: line"]
    (build.root / "robots.txt").unlink()
    assert results(build)[4].summary == "no robots.txt in the build folder"
    assert results(build)[22].status == REVIEW


def test_5_noindex(build):
    build.good().write(
        "thanks/index.html", html("/thanks/", head='<meta name="robots" content="NoIndex">')
    )
    build.write(
        "blog/index.html", html("/blog/", body='<a href="/thanks/">t</a><a href="/blog/rye/">r</a>')
    )
    result = results(build)[5]
    assert result.status == REVIEW
    assert result.evidence == ["/thanks/: noindex"]
    build.write("index.html", html("/", head='<meta name="googlebot" content="noindex,nofollow">'))
    assert results(build)[5].status == FIX


def test_7_broken_links_and_what_counts_as_internal(build):
    body = (
        '<a href="/missing/">a</a><a href="https://example.com/also-missing">b</a>'
        '<a href="https://www.example.com/blog/rye/">ok</a><a href="https://other.example.org/x">ext</a>'
        '<a href="mailto:hello@example.com">m</a><a href="tel:+1">t</a><a href="#top">h</a>'
        '<a href="/blog/rye/?utm=1#part">q</a><a href="/img/loaf.webp">file</a>'
        '<a href="../../outside/">up</a><a href="./rye/">dot</a><a href="/about">no slash</a>'
    )
    build.good().write("blog/index.html", html("/blog/", body=body + '<a href="oats/">o</a>'))
    result = results(build)[7]
    assert result.status == FIX
    assert result.evidence == [
        "blog/index.html: /missing/",
        "blog/index.html: https://example.com/also-missing",
        "blog/index.html: ../../outside/",
    ]
    without_site = results(build, site="")[7]
    assert "blog/index.html: https://example.com/also-missing" not in without_site.evidence


def test_8_canonical(build):
    build.good()
    build.write("blog/rye/index.html", html("/blog/rye/", canonical=None))
    build.write("blog/oats/index.html", html("/blog/oats/", canonical="/blog/oats/"))
    build.write("about/index.html", html("/about/", canonical="https://staging.example.net/about/"))
    build.write(
        "blog/index.html",
        html("/blog/", canonical=f"{SITE}/", body='<a href="rye/">r</a><a href="oats/">o</a>'),
    )
    result = results(build)[8]
    assert result.status == FIX
    assert sorted(result.evidence) == [
        "about/index.html: other domain: staging.example.net",
        "blog/index.html: points to /",
        "blog/oats/index.html: not an absolute https address: /blog/oats/",
        "blog/rye/index.html: 0 canonical links",
    ]


def test_8_canonical_to_another_page_is_a_review(build):
    build.good().write(
        "blog/index.html",
        html("/blog/", canonical=f"{SITE}/", body='<a href="rye/">r</a><a href="oats/">o</a>'),
    )
    result = results(build)[8]
    assert result.status == REVIEW
    assert result.evidence == ["blog/index.html: points to /"]


def test_9_descriptions(build):
    build.good()
    build.write("about/index.html", html("/about/", description=""))
    same = "The same words on two pages, long enough to look like a real description here."
    build.write("blog/rye/index.html", html("/blog/rye/", description=same))
    build.write("blog/oats/index.html", html("/blog/oats/", description=same))
    result = results(build)[9]
    assert result.status == FIX
    assert result.evidence == [
        "about/index.html: missing",
        "same description on 2 pages: blog/oats/index.html, blog/rye/index.html",
    ]


def test_9_length_is_a_note_not_a_failure(build):
    build.good().write("about/index.html", html("/about/", description="Short."))
    result = results(build)[9]
    assert result.status == OK
    assert result.summary == "present and unique on 5 pages; 1 outside 70–160 characters"


def test_10_h1_count(build):
    build.good().write("about/index.html", html("/about/", h1=None))
    build.write("blog/rye/index.html", html("/blog/rye/", body="<h1>Second</h1>"))
    result = results(build)[10]
    assert result.evidence == [
        "about/index.html: 0 h1 elements",
        "blog/rye/index.html: 2 h1 elements",
    ]


def test_11_faq_and_19_person_markup(build):
    schema = (
        '<script type="application/ld+json">{"@graph":[{"@type":["FAQPage","WebPage"]},'
        '{"@type":"Article","author":{"@type":"Person","name":"Alex Example"}}]}</script>'
    )
    build.good().write("about/index.html", html("/about/", head=schema))
    found = results(build)
    assert found[11].status == REVIEW
    assert found[11].evidence == ["about/index.html"]
    assert found[19].status == REVIEW
    assert "Person markup on 1 pages" in found[19].summary


def test_12_breadcrumbs(build):
    build.good().write("blog/rye/index.html", html("/blog/rye/", crumbs=False))
    result = results(build)[12]
    assert result.status == FIX
    assert result.summary == "1 of 2 deeper pages"
    flat = type(build)(build.root / "flat")
    flat.write("index.html", html("/", crumbs=False))
    assert results(flat)[12].status == NOT_APPLICABLE


def test_12_invalid_json_ld_does_not_crash(build):
    build.good().write(
        "blog/rye/index.html",
        html(
            "/blog/rye/", crumbs=False, head='<script type="application/ld+json">{not json</script>'
        ),
    )
    assert results(build)[12].status == FIX


def test_13_orphans(build):
    build.good().write(
        "blog/hidden/index.html", html("/blog/hidden/", body='<a href="/blog/hidden/">self</a>')
    )
    result = results(build)[13]
    assert result.status == FIX
    assert result.evidence == ["/blog/hidden/: no internal link points here"]
    (build.root / "blog/hidden/index.html").unlink()
    assert results(build)[13].summary.startswith("every page has an internal link")


def test_14_alt_and_15_images(build):
    body = (
        '<img src="/img/a.png"><img src="/img/b.webp" alt="" width="1" height="1">'
        '<img src="/img/icon.svg" alt="Icon">'
    )
    build.good().write("about/index.html", html("/about/", body=body))
    build.write("img/a.png", b"x" * 300_001)
    found = results(build)
    assert found[14].status == FIX
    assert found[14].evidence == ["about/index.html: /img/a.png"]
    assert found[15].status == FIX
    assert found[15].evidence == ["img/a.png: 300 kB"]

    build.write("img/a.png", b"x" * 10)
    build.write("about/index.html", html("/about/", body='<img src="/img/b.webp" alt="">'))
    found = results(build)
    assert found[14].status == OK
    assert 'alt=""' in found[14].summary
    assert found[15].status == REVIEW
    assert found[15].evidence == ["about/index.html: /img/b.webp"]


def test_21_history_api(build):
    script = (
        "<script>window.addEventListener('load', () => history.pushState({}, '', '/x'));</script>"
    )
    build.good().write("about/index.html", html("/about/", body=script))
    result = results(build)[21]
    assert result.status == REVIEW
    assert result.evidence == ["about/index.html"]


def test_22_ai_bots(build):
    result = results(build.good())[22]
    assert result.status == OK
    assert "search    OAI-SearchBot: allowed (by the * group)" in result.evidence
    assert "training  GPTBot: blocked" in result.evidence
    assert "training  CCBot: allowed (by the * group)" in result.evidence
    build.write("robots.txt", "User-agent: OAI-SearchBot\nUser-agent: PerplexityBot\nDisallow: /\n")
    result = results(build)[22]
    assert result.status == FIX
    assert result.summary == "search crawlers blocked: OAI-SearchBot, PerplexityBot"
    assert "search    Googlebot: not mentioned" in result.evidence


def test_bot_access_rules():
    assert bot_access("", "GPTBot") == "not mentioned"
    assert bot_access("User-agent: *\nDisallow:\n", "GPTBot") == "allowed (by the * group)"
    assert (
        bot_access("User-agent: gptbot # ours\nDisallow: /private/\n", "GPTBot") == "partly blocked"
    )
    assert bot_access("User-agent: GPTBot\nDisallow: /\nAllow: /\n", "GPTBot") == "partly blocked"
    assert bot_access("User-agent: GPTBot\nDisallow: /*\n", "GPTBot") == "blocked"
    two = "User-agent: A\nDisallow: /\n\nUser-agent: GPTBot\nAllow: /\nnonsense line\n"
    assert bot_access(two, "GPTBot") == "allowed"
    assert bot_access(two, "A") == "blocked"


def test_23_snippet_controls(build):
    head = '<meta name="robots" content="max-snippet:0, noarchive">'
    build.good().write(
        "about/index.html", html("/about/", head=head, body="<p data-nosnippet>x</p>")
    )
    build.write(
        "blog/rye/index.html",
        html("/blog/rye/", head='<meta name="robots" content="max-snippet:50">'),
    )
    result = results(build)[23]
    assert result.status == REVIEW
    assert result.evidence == ["about/index.html: max-snippet:0, noarchive, data-nosnippet ×1"]


def test_redirect_pages_and_404_are_not_judged(build):
    build.good().write(
        "old/index.html", '<html><head><meta http-equiv="refresh" content="0;url=/"></head></html>'
    )
    build.write("404.html", "<html><body><h1>Not found</h1></body></html>")
    found = results(build)
    for number in (1, 2, 8, 9, 10, 13):
        assert found[number].status == OK, found[number]


def test_a_site_under_a_base_path(build):
    base = "/docs"
    body = '<a href="/docs/guide/">g</a><a href="/docs/missing/">m</a><a href="/elsewhere/">e</a>'
    build.write("index.html", html("/", canonical=f"{SITE}{base}/", crumbs=False, body=body))
    build.write("guide/index.html", html("/guide/", canonical=f"{SITE}{base}/guide/", crumbs=False))
    build.write("robots.txt", ROBOTS)
    build.write("sitemap-0.xml", sitemap(f"{base}/", f"{base}/guide/", "/other/"))
    found = results(build, site=f"{SITE}{base}/")
    assert found[7].evidence == ["index.html: /docs/missing/"]
    assert found[8].status == OK, found[8]
    assert found[2].evidence == [f"{SITE}/other/: in the sitemap, outside the site's base path"]
    assert found[13].status == OK, found[13]


def test_url_paths():
    assert url_path_of("index.html") == "/"
    assert url_path_of("blog/rye/index.html") == "/blog/rye/"
    assert url_path_of("blog/rye.html") == "/blog/rye"


def test_symlinks_are_not_followed(build, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    (outside / "secret.html").write_text("<html></html>", encoding="utf-8")
    build.good()
    (build.root / "linked").symlink_to(outside, target_is_directory=True)
    site = load(build.root, SITE)
    assert not any("secret" in name for name in site.files)


def test_statuses_are_the_documented_five():
    assert {checks.OK, checks.FIX, checks.REVIEW, checks.NOT_APPLICABLE, checks.NOT_CHECKED} == {
        "OK",
        "FIX",
        "REVIEW",
        "N/A",
        "NOT CHECKED",
    }

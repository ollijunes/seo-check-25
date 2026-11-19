import json
import subprocess
import sys

import pytest

from seo_check import cli
from tests.conftest import SITE, html


def test_report_for_a_clean_site(build, capsys):
    assert cli.main([str(build.good().root), "--site", SITE, "--strict"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[0] == (
        " 1  OK           Content is in the HTML without JavaScript: "
        "every indexable page has text in the raw HTML; no file over 2 MB"
    )
    assert " 3  NOT CHECKED  Sitemap submitted to Search Console" in out
    assert "11  N/A          FAQ content is visible text: no FAQPage markup found" in out
    assert "      search    OAI-SearchBot: allowed (by the * group)" in out
    assert "      and 5 more (--all shows them)" in out
    assert lines[-1] == (
        "5 pages. 0 to fix, 0 to review, 10 not checked here: "
        "those need the live site, the owner or a reader."
    )


def test_strict_fails_on_a_finding_and_evidence_is_capped(build, capsys):
    build.good()
    for index in range(7):
        build.write(f"p{index}/index.html", html(f"/p{index}/", h1=None, crumbs=False))
    assert cli.main([str(build.root), "--site", SITE]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "10  FIX          One h1 per page: 7 pages" in out
    assert "      and 2 more (--all shows them)" in out
    assert cli.main([str(build.root), "--site", SITE, "--strict", "--all"]) == cli.EXIT_FIX
    assert "more (--all shows them)" not in capsys.readouterr().out


def test_json(build, capsys):
    assert cli.main([str(build.good().root), "--json"]) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pages"] == 5
    assert payload["summary"] == {"fix": 0, "review": 0, "not_checked": 10}
    assert payload["results"][3] == {
        "number": 4,
        "title": "robots.txt lets Googlebot in",
        "status": "OK",
        "summary": "Googlebot allowed (by the * group); Sitemap line present",
        "evidence": [],
    }


def test_errors(tmp_path, capsys):
    assert cli.main([str(tmp_path / "nope")]) == cli.EXIT_ERROR
    assert "not a folder" in capsys.readouterr().err
    assert cli.main([str(tmp_path)]) == cli.EXIT_ERROR
    assert "no .html files" in capsys.readouterr().err


def test_version_and_module_entry_point(build):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 0
    result = subprocess.run(
        [sys.executable, "-m", "seo_check", str(build.good().root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "5 pages." in result.stdout

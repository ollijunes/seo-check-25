import json

import pytest

from seo_check.evidence import main

PAGE = "https://example.com/article/"


def scrape():
    return {
        "success": True,
        "data": {
            "metadata": {"sourceURL": PAGE, "url": PAGE, "statusCode": 200, "title": "Bread"},
            "markdown": "A loaf.",
        },
    }


def audit():
    return {
        "url": PAGE,
        "crawledPages": 1,
        "overallScore": 72,
        "categoryResults": [
            {
                "categoryId": "core",
                "passCount": 2,
                "failCount": 1,
                "warnCount": 0,
                "notMeasuredCount": 3,
                "advisoryCount": 1,
            }
        ],
    }


def test_two_sources_report_the_same_page(tmp_path, capsys):
    options = [PAGE]
    for flag, report in [("--firecrawl", scrape()), ("--seomator", audit())]:
        path = tmp_path / flag[2:]
        path.write_text(json.dumps(report))
        options.extend([flag, str(path)])
    assert main(options) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["firecrawl"]["markdown_characters"] == 7
    assert output["seomator"]["categories"][0]["notMeasuredCount"] == 3
    assert output["seomator"]["categories"][0]["advisoryCount"] == 1
    assert output["seomator"]["score"] == 72


@pytest.mark.parametrize(
    ("flag", "report"),
    [
        ("--firecrawl", {"success": False}),
        ("--firecrawl", {**scrape(), "data": {**scrape()["data"], "blocked": True}}),
        ("--firecrawl", {**scrape(), "data": {**scrape()["data"], "markdown": " "}}),
        ("--firecrawl", []),
        ("--seomator", {**audit(), "crawledPages": 2}),
        ("--seomator", {**audit(), "run": {"crawl": True}}),
        ("--seomator", {**audit(), "url": PAGE + "?edition=2"}),
        ("--seomator", {**audit(), "overallScore": 105}),
        ("--seomator", {**audit(), "categoryResults": []}),
        ("--seomator", {"error": {"message": "Failed"}}),
    ],
)
def test_invalid_evidence_has_no_output(tmp_path, capsys, flag, report):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert main([PAGE, flag, str(path)]) == 2
    assert capsys.readouterr().out == ""


def test_unavailable_file_and_invalid_input(tmp_path):
    assert main([PAGE, "--firecrawl", str(tmp_path / "missing")]) == 2
    path = tmp_path / "report.json"
    path.write_text("truncated")
    assert main([PAGE, "--seomator", str(path)]) == 2
    with pytest.raises(SystemExit) as exc:
        main([PAGE])
    assert exc.value.code == 2

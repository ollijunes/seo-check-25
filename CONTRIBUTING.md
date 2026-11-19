# Contributing

Corrections are welcome, most of all where a search engine has changed its
documentation and the skill is out of date. Link the search engine's own
page. A blog post about the change is not a source.

```sh
uv sync --locked
uv run python -m pytest --cov=seo_check --cov-fail-under=90
uv run ruff check .
uv run ruff format --check .
gitleaks git --redact --no-banner .
python3 scripts/check_public_tree.py
```

## Rules

- The list stays at 25 points and the numbers do not move. Reports from
  different dates must be comparable.
- A fact in the skill carries its source and the month it was checked. A
  claim no search engine has confirmed goes under "Not confirmed", or out.
- The checker reads a folder. No network requests, no writes, no
  dependencies outside the Python standard library.
- A check answers `FIX` only when the build proves the problem. When a
  person has to decide, it answers `REVIEW`. When it cannot know, it
  answers `NOT CHECKED`. Do not turn a guess into a verdict.
- Keep the English and the Finnish skill in step. Change both in the same
  pull request.
- No real sites in examples or tests. Use `example.com` and invented text.

Use a public-safe Git author address. Report vulnerabilities through
[SECURITY.md](SECURITY.md), not a public issue.

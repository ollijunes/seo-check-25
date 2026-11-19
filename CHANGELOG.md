# Changelog

## 0.1.0

- The 25-point skill in English (`skills/seo-check-25`) and Finnish
  (`skills/seo-tarkistus-25`): a method and a passing condition for every
  point, limits on what the agent may touch, a report format, and sources
  with the month they were checked.
- `seo-check`: reads a built site, answers 14 of the 25 points and flags
  three more for a reader: text
  in the raw HTML and file sizes, sitemap, robots.txt, noindex, broken
  internal links, canonical, meta descriptions, h1, FAQPage and Person
  markup, breadcrumbs, orphan pages, alt text, image formats, inline
  history manipulation, AI crawler access and snippet controls.
- Statuses OK, FIX, REVIEW, N/A and NOT CHECKED, with evidence for each.
  `--strict` for CI, `--json`, `--all`.
- Tests on Linux and macOS with Python 3.11–3.14, and a privacy scan of the
  full history in CI.

---
name: seo-check-25
description: Technical and content SEO check for any website in 25 points - server-side rendering, sitemap, Search Console, robots.txt and AI crawlers, noindex, redirect chains, 404s, canonical, meta descriptions, one h1, FAQ content, breadcrumbs, orphan pages, alt text, image formats, CLS/INP/LCP, machine-sounding text, author, backlinks, spam policies, snippet controls, main content, Bing. Use when asked for an SEO review, an SEO audit of a site or a build, "check the site for SEO", or before a site goes live.
---

# SEO check: 25 points

Go through every point in order. For each one report a status, the evidence (a command, a URL or a file and line) and the fix.

Statuses: **OK / FIX / REVIEW / N/A / NOT CHECKED**. Never mark a point OK without evidence. NOT CHECKED is an honest answer; say why.

Points 1–20 are the base check. Points 21–25 cover spam policies and how search engines and AI features use a page. Points 9, 10 and 14 are hygiene: report them, but do not put them at the top of the summary. The top is indexability, content quality and spam policies.

## Limits (read first)

- **The check reads. It changes nothing.** Do not edit production robots.txt, noindex, redirects, server config, DNS or deployments as a side effect. Fixes go to a branch and a pull request. Deploying needs the owner's go-ahead.
- **A preview behind a password is noindex on purpose.** If the site is behind basic auth before launch, check indexability from the build output (`dist/robots.txt`, the robots meta in the HTML), not from the live headers. Say so in the report.
- **Submitting to Search Console or Bing, and asking for backlinks, are the owner's actions.** Prepare them (sitemap URL, list, draft messages). Do not submit and do not contact third parties.
- **Load:** at most two parallel requests to production. Use the build folder whenever there is one.
- Read the repository's own `AGENTS.md` or `CLAUDE.md` and follow it.

## Start

1. Domain, repository and build command (Astro: `npm run build` writes `dist/`).
2. Page list: `dist/sitemap*.xml` or `find dist -name index.html`.
3. If `seo-check` is installed, run it on the build first. It answers the points it can and lists the rest:
   ```sh
   seo-check dist --site https://example.com
   ```
4. Access to Search Console, Bing Webmaster Tools and a backlink index, if the owner has given it.

## Evidence from a published page

For an optional live check, install [Firecrawl Local](https://crates.io/crates/firecrawl-local)
and [SEOmator](https://github.com/seo-skills/seo-audit-skill). These commands were tested
with Firecrawl Local 0.1.1 and SEOmator 8.0.1. Run them in an empty working directory,
one after the other.

```sh
page=https://example.com/
FIRECRAWL_CLOUD=off firecrawl-local scrape --public-only --browser never \
  --format markdown "$page" > page.json
seomator audit "$page" --categories core,images,content,schema,htmlval \
  --concurrency 1 --no-cwv --no-save --fail-under 0 --format json > audit.json
seo-check-evidence "$page" --firecrawl page.json --seomator audit.json
```

Firecrawl extracts the page text. SEOmator fetches the page, robots.txt and available
sitemaps and checks the selected categories. The combined JSON shows the source URL,
HTTP status, extraction length and rule counts for each category. Either input can be
used on its own. Read the original reports for the extracted text and individual rule
IDs. Use each finding as evidence for that page and checklist point. Search Console,
field performance and site-wide checks need their own data.

## The points

| # | Point | How to check | Passes when |
|---|---|---|---|
| 1 | Render it server-side | `curl -s URL \| grep -c '<h1'`. Text and links are in the HTML without JavaScript, including prices, FAQ answers, tabs and expandable sections. Googlebot reads the first 2 MB (uncompressed) of an HTML, CSS or JS file: `curl -s URL \| wc -c`, and the sizes of the bundles; put the important content early. JavaScript rules: noindex is not added by JS, the canonical is not changed by JS, the robots meta is in `<head>`. Assume AI crawlers do not run JavaScript. | Main content, h1, links and meta are plain text in the HTML; files under 2 MB |
| 2 | Generate a sitemap | `curl -sI /sitemap.xml`. Compare the URL list with the page list. No noindex, redirect or 404 URLs. | Every canonical 200 page is listed, `lastmod` is sane |
| 3 | Submit it to Search Console | Search Console or the owner's confirmation. Domain property verified. Read the page indexing states: "Crawled, currently not indexed", "Discovered, currently not indexed", "Soft 404", "Duplicate without user-selected canonical". | Sitemap submitted with status Success; the problem states are explained. Otherwise: write the steps for the owner |
| 4 | Unblock Googlebot in robots.txt | `curl -s /robots.txt`. No `Disallow: /` for Googlebot. A `Sitemap:` line. Blocking Googlebot also removes the page from Google's AI features. `Google-Extended` only controls use for Gemini training and grounding; it does not affect Search. AI crawlers: point 22. | Googlebot reaches every public path; CSS and JS are allowed |
| 5 | Delete the noindex tags | `grep -rl 'noindex' dist`; `curl -sI` shows no `X-Robots-Tag: noindex` on public pages. | noindex only where intended (404, thank-you, search results) |
| 6 | Kill the redirect chains | `curl -sIL -o /dev/null -w '%{num_redirects} %{url_effective}'` for old URLs and for the www and http forms. | At most one hop, 301, straight to the final URL |
| 7 | Fix the 404s | Internal links: collect every `href` from the build and check that the target exists. Backlink index: broken inbound links. | No internal 404s; valuable old URLs redirect with 301 |
| 8 | Add canonical tags | One `<link rel="canonical">` per page: absolute, https, the right domain, the page's own URL, trailing slash used the same way everywhere. | One per page, pointing to itself (except where intended) |
| 9 | Write a meta description for every page | Collect `meta[name=description]`: missing and duplicates. | Each page has its own, roughly 120–160 characters |
| 10 | One h1 per page | `grep -o '<h1' file \| wc -l` per page. | Exactly one |
| 11 | FAQ content (FAQ markup optional) | Google stopped showing FAQ rich results on 7 May 2026. `FAQPage` is still a valid schema.org type. Check that the questions and answers are visible text, not behind JavaScript, and that any `FAQPage` markup matches them; validate the JSON. Do not add new FAQPage markup for the sake of a rich result. Do not remove markup that works. | Visible FAQ text; any markup is valid and agrees with the text |
| 12 | Add breadcrumbs | A visible breadcrumb trail and `BreadcrumbList` JSON-LD on pages below the first level. | On every page at level two and deeper |
| 13 | Link the orphan pages | URLs in the sitemap that no internal link points to. | No orphans; aim for two internal links to each page |
| 14 | Alt text on every image | `<img>` without `alt`, or with an empty `alt` on a content image. | Descriptive alt on content images, `alt=""` on decoration |
| 15 | Convert images to WebP | File types and sizes in the build; list images over 300 kB. | Content images are WebP or AVIF, with `width` and `height`, lazy-loaded below the fold |
| 16 | Fix the layout shifts | Field data first: CrUX, PageSpeed Insights or Search Console Core Web Vitals, 75th percentile. Lab tools for finding the cause. Fonts with `font-display`, sizes on images. Also INP: heavy event handlers, third-party scripts. | CLS ≤ 0.1 and INP ≤ 200 ms at p75 in field data |
| 17 | Load fast | LCP in field data; TTFB with `curl -w '%{time_starttransfer}'`. Core Web Vitals are part of page experience, not a strong ranking signal on their own. Do not promise a ranking gain. | LCP ≤ 2.5 s at p75 in field data |
| 18 | Remove the obvious AI slop | Read the content pages. Run a style checker for the language if one exists. Everything generated is reviewed by a person before publishing, including titles, meta descriptions, JSON-LD and alt text. Ask for proof of the review, not a score. See point 24. | No invented facts; generated text and metadata reviewed by a person |
| 19 | Add a real author bio | An author page with name, background, photo and contact; `Person` markup; articles name the author and link to the page. | A real person with details that can be checked. Nothing invented |
| 20 | Get quality backlinks | Backlink index: referring domains, competitors' links, unlinked brand mentions. | A list of ten realistic targets with a reason for each. No bought links |
| 21 | Spam policies | Read Google's spam policies and check each: (a) scaled content abuse: pages mass-produced from a feed or a template without added value; (b) expired domain abuse; (c) doorway pages: area pages where only the place name changes; (d) cloaking: `curl -A Googlebot` against a browser, same content; (e) sneaky redirects; (f) back-button hijacking: `grep -rE 'history\.(push\|replace)State' dist` and history changes on page load; (g) site reputation abuse: third-party content in a subfolder without editorial control; (h) bought links, keyword stuffing, scraping; (i) reviews: no incentivised reviews without disclosure. | No hits. Every hit is a blocking finding |
| 22 | AI crawler access | robots.txt and the firewall or CDN. Report a table. **Search crawlers, allow them if the goal is visibility:** `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `Googlebot`, `Bingbot`. **Training crawlers, a business decision, record it:** `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`. **User-triggered fetchers** (`ChatGPT-User`, `Claude-User`, `Perplexity-User`) may not follow robots.txt; control them at the firewall. Status for each: allowed, blocked, not mentioned. Check that a CDN's "block AI bots" switch or managed robots.txt is not on by accident. Test real access: `curl -s -o /dev/null -w '%{http_code}' -A "OAI-SearchBot" URL`, compare with a browser: no 403, no JavaScript challenge. Check the user-agent names against each vendor's current documentation on every run. | Search crawlers get 200 and the same content; the state of the training crawlers is a decision someone made |
| 23 | Snippet controls | `grep -rEo 'nosnippet\|data-nosnippet\|max-snippet[^"]*\|max-image-preview[^"]*\|noarchive\|unavailable_after' dist` and the `X-Robots-Tag` headers. `nosnippet` and `max-snippet:0` also limit how Google's AI features can use the page. | No accidental nosnippet or max-snippet:0 on public pages |
| 24 | Main content | Read the money pages and the key articles on four axes. **Effort:** is human work visible, or was the page assembled from a feed or generated unattended? A citation does not replace own work. **Originality:** is there something the top results do not already have: own data, experience, a calculator, a photo? **Talent or skill:** clear writing, tools that work. **Accuracy:** figures and claims checked, most of all on money, law and health. Tabs, expandable sections and user comments count as main content, so they must be in the raw HTML (point 1). | A reasoned verdict on the four axes for every key page, with evidence; weak ones go on the fix list |
| 25 | Bing index | Bing Webmaster Tools: site verified, sitemap submitted, IndexNow in use, pages indexed. Copilot cites from Bing's index. Verification and submission are the owner's actions: write the steps. | Verified and submitted. Otherwise: steps for the owner |

## Report

Write the report into the repository (for example `docs/seo/seo-check-YYYY-MM-DD.md`), or to the path given in the task if you may not write there.

1. Summary: the three to five fixes that matter most, in order of effect.
2. A table of the 25 points: status, evidence, fix, size of the work (S/M/L).
3. Blocking findings apart from the rest: anything that stops indexing, broken redirects, spam policy hits, blocked search crawlers.
4. What was not checked, and why.
5. If traffic has moved: compare the dates with Google's Search Status Dashboard and call a match a **hypothesis**, not a cause, most of all when update windows overlap.

When you fix: a branch, one point per commit or a sensible group, build and tests, a pull request. No deployment without the owner's go-ahead.

## Sources and confidence

Checked against the search engines' and crawler vendors' own pages on 19 November 2026. Search engines change their documentation; check a claim against the original before you repeat it in a customer report.

**From Google's own documentation and blog:** Googlebot reads the first 2 MB of each HTML, CSS or JS file, uncompressed and including the HTTP headers; PDFs 64 MB (Googlebot documentation and the Search Central blog, March 2026). FAQ rich results ended on 7 May 2026, and Google has removed their documentation (Search Central changelog). The AI optimization guide on Search Central (May 2026) says Google's AI features use the same ranking and quality systems as Search, and that special files, markup or text chunking are not needed for them, and points to the Generative AI performance report in Search Console. Back-button hijacking is named in the spam policies. The AI features documentation says snippet controls and Googlebot access govern use in AI features. Core Web Vitals thresholds: LCP 2.5 s, INP 200 ms, CLS 0.1.

**From the vendors' crawler documentation:** OpenAI, Anthropic and Perplexity run separate crawlers for search, training and user-triggered fetches. The names in point 22 were checked on 19 November 2026.

**Not confirmed by any search engine, do not use as a reason:** percentages for how often AI answers cite a given kind of page, freshness multipliers, claims that a single Core Web Vital became a ranking signal on a certain date, and the claim that ChatGPT Search runs on Bing's index.

**Not in this check:** hreflang, local SEO and business profiles, migrations, consent banners and measurement, image and video search, and the quality of the backlink profile.

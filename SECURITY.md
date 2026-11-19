# Security

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/ollijunes/seo-check-25/security/advisories/new).
Do not put a customer's site, report or unpublished pages in a public
issue. A small invented page that shows the problem is enough.

## What the checker does

- Reads the files in the build folder you name and prints a report. It
  writes no files and changes nothing.
- Makes no network requests. `--site` is only used to tell internal links
  from external ones.
- Does not follow symbolic links, and reads at most 20 MB of each HTML
  file.
- Parses HTML and JSON-LD as data. It runs no scripts from the pages.
- No subprocesses and no dependencies outside the Python standard library.
- The report quotes file names, link targets and robots directives from the
  build. In CI those lines end up in the build log.

## What the skill is

The files under `skills/` are instructions for a language model. They
contain no code. Read a skill before you install it: an agent follows what
it says. These two tell the agent to read only, to send at most two
parallel requests to a production site, and to leave Search Console,
deployments and outside contacts to the site's owner. They include `curl`
lines that fetch pages with a crawler's user-agent name, to compare what a
crawler and a browser receive. Run them against sites you own or have
permission to test.

## Repository hygiene

Every page the tests build is invented and uses `example.com`. CI scans the
full Git history with Gitleaks and with `scripts/check_public_tree.py`,
which looks for private network addresses, home-directory paths, email
addresses outside example domains and private files. Automated scans
support a manual review; they do not prove that nothing private slipped in.

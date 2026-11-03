# IRIS Lab website

**I**ntelligent systems **R**obustness, **I**nterpretability, and **S**ecurity Lab,
Department of Computer Science, The University of Texas at Dallas.

Live site: <https://iris-research-lab.github.io>

Plain HTML + Bootstrap 5.3 + Font Awesome. Content is edited only in the private
[IRIS-Updates repository](https://github.com/IRIS-Research-Lab/IRIS-Updates/tree/main/data).
See [CONTRIBUTING.md](CONTRIBUTING.md) for fields and images.

## Layout

```
index.html, people/, research/, publications/, join/, 404.html   pages
partials/            navbar and footer, injected by assets/js/layout.js
assets/js/           one script per page + common.js helpers
schemas/             JSON Schemas for the shared content
scripts/build.py     fetch, validate, and assemble _site/ for GitHub Pages
scripts/validate.py  schema + uniqueness + local image checks
_site/data/          generated content from IRIS-Updates; never edit or commit
```

## Shared data and deployment

`IRIS-Updates/data/{news,people,pubs,research}.json` is the single source of truth. It is private, so
browsers cannot fetch it directly. The Pages workflow fetches the four files using `IRIS_UPDATES_TOKEN`,
resolving `main` to one commit first, validates them, and copies their exact bytes into `_site/data/`.
Only static pages, assets, partials, schemas, `.nojekyll`, and these four JSON files are published.

The existing page scripts still load `/data/*.json`. Existing consumers such as hoak.me keep using
`https://iris-research-lab.github.io/data/pubs.json` and `people.json`; URLs, CORS behavior on Pages,
publication keys, person IDs, and absolute image URLs stay stable.

A source merge dispatches the Pages workflow using the source repository's `LAB_SITE_DISPATCH_TOKEN`.
Website merges and an hourly recovery schedule also build from the latest source `main`. Scheduled
runs can be delayed or disabled after 60 inactive days on a public repo, so source dispatch is the primary
refresh mechanism. There are no content-sync commits or submodule updates to make.

A missing token, unreachable source, missing file, invalid JSON, schema error, duplicate ID/key, or
missing local image fails the build before an artifact is uploaded. The previous live deployment stays
available. No stale fallback is silently published. PR checks use `--published` to validate the current
public snapshot without exposing the private source token to PR code; they do not validate proposed
IRIS-Updates changes. Production always fetches the private source and validates it again.

## Local preview and checks

With an authenticated clone of IRIS-Updates alongside this checkout:

```sh
python3 -m pip install 'jsonschema[format]>=4.18'
python3 scripts/build.py --data-dir ../IRIS-Updates/data
python3 -m unittest discover -s tests
python3 -m http.server 8000 --directory _site
```

Open <http://localhost:8000>. Images pointing at this site are served from your build. Rebuild after
editing either checkout. To fetch the private source instead, set `IRIS_UPDATES_TOKEN` in your environment
and run `python3 scripts/build.py`. Never put the token in a file committed to either repository.
`python3 scripts/validate.py` validates the generated `_site/data/` without fetching.

## One-time setup and merge order

1. Merge the **IRIS-Updates migration PR first**.
2. In this repository, set the Actions secret `IRIS_UPDATES_TOKEN`: a fine-grained PAT with **Contents:
   read** on IRIS-Updates. The default `GITHUB_TOKEN` cannot read the private source repository.
3. In IRIS-Updates, set `LAB_SITE_DISPATCH_TOKEN`: a fine-grained PAT with **Actions: write** on this
   repository. Authorize the tokens for the organization if required. This requests a workflow; it cannot
   edit website content.
4. Coordinate switching Settings → Pages → Source to **GitHub Actions** with merging this PR. The old
   branch publisher cannot assemble the external content. The merge then runs `.github/workflows/pages.yml`.

No visibility change is needed. The four content files remain public in the built site. No secrets,
Pages settings, or deployments are changed while preparing these PRs. If the initial source refresh
fails before this workflow exists on main, the website merge supplies the first build automatically.

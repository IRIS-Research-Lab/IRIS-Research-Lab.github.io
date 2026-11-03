# IRIS Lab website

**I**ntelligent systems **R**obustness, **I**nterpretability, and **S**ecurity Lab,
Department of Computer Science, The University of Texas at Dallas.

Live site: <https://iris-research-lab.github.io>

Plain HTML + Bootstrap 5.3 + Font Awesome. Pages load their content from JSON in [`data/`](data/). There is no
build step. **Want to add a paper, yourself, or news? See [CONTRIBUTING.md](CONTRIBUTING.md).**

## Layout

```
index.html, people/, research/, publications/, join/, 404.html   pages
partials/            navbar and footer, injected by assets/js/layout.js
assets/js/           one script per page + common.js helpers
data/                site content (the single source of truth)
schemas/             JSON Schemas for each data file
scripts/validate.py  schema + uniqueness + image checks (runs in CI on every PR)
```

## Shared data

`data/pubs.json` and `data/people.json` are the single source of truth for lab publications and members,
and are also fetched at runtime by <https://www.hoak.me>. GitHub Pages serves them with
`Access-Control-Allow-Origin: *`:

```js
const pubs = await fetch('https://iris-research-lab.github.io/data/pubs.json').then(r => r.json());
```

Keep these URLs, publication `key`s and person `id`s stable. Image URLs in the data are absolute so they
work from either site.

## Local preview

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

When previewing locally, image URLs pointing at this site are served from your working copy.

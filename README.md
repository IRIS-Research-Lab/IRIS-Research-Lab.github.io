# IRIS Lab website

**I**ntelligent systems **R**obustness, **I**nterpretability, and **S**ecurity Lab,
Department of Computer Science, The University of Texas at Dallas.

Live site: <https://iris-research-lab.github.io>

Plain HTML, CSS, and JavaScript. All content and assets are edited and reviewed in
this website repository: `data/news.json`, `data/people.json`, `data/pubs.json`,
`data/research.json`, `data/lab_media.json`, and `assets/`. Field details are in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Local preview

From this repository:

```sh
uv venv
uv pip install 'jsonschema[format]>=4.18'
uv run python scripts/build.py
uv run python scripts/validate.py
uv run python -m unittest discover -s tests
uv run python -m http.server 8000 --directory _site
```

Open <http://localhost:8000>. Builds and validation use local files with no token
or network access (install the Python validation dependency once beforehand).
`--data-dir /path/to/data` optionally overrides the four content JSON files only;
assets and `lab_media.json` always come from this website checkout.

Pushes to `main` and manual dispatches publish the site. Pull requests run the same
local build and full test suite; the required job is named **validate**. Public
`/data/*.json` paths stay unchanged. Keep publication keys, person IDs, and public
asset URLs stable for hoak.me consumers.

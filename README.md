# IRIS Lab website

**I**ntelligent systems **R**obustness, **I**nterpretability, and **S**ecurity Lab,
Department of Computer Science, The University of Texas at Dallas.

Live site: <https://iris-research-lab.github.io>

Plain HTML and CSS in the V3 North Star system (dark field, mint links, figure-and-citation
publication rows). News, people, and publications are edited in the private
[IRIS-Updates](https://github.com/IRIS-Research-Lab/IRIS-Updates) repository and copied
into the site at build time. Lab photos and videos live here
(`data/lab_media.json`, `assets/media/lab/`). Field details are in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Local preview

With an IRIS-Updates checkout alongside this repo:

```sh
uv venv
uv pip install 'jsonschema[format]>=4.18'
uv run python scripts/build.py --data-dir ../IRIS-Updates/data
uv run python -m unittest discover -s tests
uv run python -m http.server 8000 --directory _site
```

Open <http://localhost:8000>. To build from the private source instead of a local
checkout, set `IRIS_UPDATES_TOKEN` and run `uv run python scripts/build.py`. Pull
request checks run `python scripts/build.py --published` with pip, which validates
the current public snapshot without that token.

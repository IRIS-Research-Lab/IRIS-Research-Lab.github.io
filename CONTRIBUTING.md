# Contributing to the IRIS Lab website

News, people, publications, and research themes come from the JSON files in the private
[IRIS-Updates repository](https://github.com/IRIS-Research-Lab/IRIS-Updates/tree/main/data).
Edit that content and add new publication figures there; legacy website images remain here. The website generates those public `/data/` files at build time;
do not copy them into this repository. Lab photos and videos are the exception, listed below.
Please don't edit the HTML/JS unless we've talked about it.

| To change...          | Edit                                   | Images go in                       |
|-----------------------|----------------------------------------|------------------------------------|
| Publications          | [`data/pubs.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/pubs.json)     | IRIS-Updates `assets/images/publications/` |
| People                | [`data/people.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/people.json) | `assets/images/people/`            |
| News on the home page | [`data/news.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/news.json)     | —                                  |
| Research themes       | [`data/research.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/research.json) | —                              |
| Lab photos and videos | [`data/lab_media.json`](data/lab_media.json) in **this** repo | `assets/media/lab/YYYY-MM-DD/` |

> ⚠️ `data/pubs.json` and `data/people.json` are also loaded by Prof. Hoak's personal site (hoak.me).
> **Never rename or delete a publication `key` or person `id`** once it has been merged, and don't move or
> rename the files in `IRIS-Updates/data/`. The public website URLs remain unchanged.

## Workflow

1. In **IRIS-Updates**, create a branch: `git checkout -b add-<something>` (or use GitHub's web editor, which does this for you).
2. Make your edit. Mind the commas: every item in a list is separated by `,` except the last one.
3. Check it locally from your **website checkout** (with IRIS-Updates alongside it):
   ```sh
   uv venv
   uv pip install 'jsonschema[format]>=4.18'
   uv run python scripts/build.py --data-dir ../IRIS-Updates/data
   ```
4. Preview locally (optional): `uv run python -m http.server 8000 --directory _site` from the website repo root, then open
   <http://localhost:8000>.
5. Open a pull request in **IRIS-Updates**. Prof. Hoak (or another lab member) should review it before
   merge. The source merge requests a website build; its validation must pass before publication. If
   it fails, inspect the website Actions log and fix the source. For a new publication image, commit it under `assets/images/publications/` in the same source PR,
   then reference its absolute public site URL. Avoid legacy website asset names. Website code PRs
   retain the **validate** check, which builds against the current public snapshot without private credentials.

## Add a paper

Add an object to `data/pubs.json` (the site sorts by year descending, preserving file order within a year):

```json
{
  "key": "mukherjee_example_2027",
  "title": "A Descriptive Paper Title",
  "authors": "Abhirup Mukherjee and Charles Dardaman and Blaine Hoak",
  "venue": "IEEE Conference on Secure and Trustworthy Machine Learning (SaTML)",
  "year": 2027,
  "group": "conference",
  "lab": true,
  "image": "https://iris-research-lab.github.io/assets/images/publications/2027_example.png",
  "links": [
    { "label": "Paper", "url": "https://arxiv.org/abs/XXXX.XXXXX" },
    { "label": "Code", "url": "https://github.com/IRIS-Research-Lab/example" }
  ]
}
```

- **`key`**: `firstauthorlastname_keyword_year`, lowercase letters, numbers and `_` only. Must be unique.
- **`authors`**: full names joined with ` and `. Use the same spelling as `data/people.json` so lab members
  other than Blaine Hoak are bolded. For equal contribution, add `*` after the names and `"authornote": "* indicates equal contribution"`.
- **`group`**: `conference`, `journal`, `workshop`, `techreport`, `thesis`, or `submission`.
  Papers under review use `submission` and `"show_lab": false`; switch the group once accepted.
  A `thesis` is hidden by default; set `show_lab: true` only for a thesis confirmed public and intended for Research.
- **`lab`**: `true` for work done in the IRIS Lab.
- **`show_lab`** (optional boolean): lab-site display flag and the source of truth. `true` lists the entry;
  `false` hides it. Year does not hide an entry. When omitted, a published group is listed and a
  `submission` stays hidden. `group: thesis` requires explicit `show_lab: true` to be listed; the legacy `show` alias does not enable a thesis. A personal site
  does not read this field. **`show`** is a deprecated alias for the same flag, accepted so a snapshot
  from before the rename still validates. When both are set, `show_lab` wins. New records set only
  `show_lab`.

- **`research_example`** (optional boolean): marks selected prior work as example content without changing
  `lab` affiliation. It does not by itself select papers for Research.
- **`highlight`** (optional boolean): selects work for hoak.me highlights and Home Featured work.
  Home lists every highlighted, lab-visible published paper, by year descending then file order;
  it excludes theses and submissions even when explicitly visible on Research. Omitted or false
  means not featured. This flag does not change IRIS Research visibility. A missing image uses
  the existing full-width citation (`nofig`) without an empty figure or caption.
- **`image`** (optional): a teaser figure, about 1200px wide, under 2 MiB (PNG/JPEG/WebP/GIF). Commit the file to
  IRIS-Updates `assets/images/publications/` and use the full `https://iris-research-lab.github.io/...` URL.
- **`links`** (optional): common labels get icons automatically: Paper, Code, Dataset, Poster, Slides,
  Talk, Blog. Put posters/slides PDFs in a public place (e.g. the arXiv page or a repo) and link them.
- Optional extras: `"award": "Best Paper Award"`, `"talkbadge": "Selected for Oral Presentation"`.

## Add yourself

1. Add a photo to `assets/images/people/<your-id>.jpg`: square-ish, about 600×600px, under 300 KB.
2. Add an object to `data/people.json`:

```json
{
  "id": "jane-doe",
  "name": "Jane Doe",
  "role": "phd",
  "start": "Fall 2026",
  "end": "In progress",
  "photo": "https://iris-research-lab.github.io/assets/images/people/jane-doe.jpg",
  "interests": ["Adversarial robustness", "Vision models"],
  "links": {
    "website": "https://janedoe.github.io",
    "scholar": "https://scholar.google.com/citations?user=XXXXXXX",
    "github": "https://github.com/janedoe",
    "linkedin": "https://www.linkedin.com/in/janedoe"
  }
}
```

- **`id`**: `firstname-lastname`, lowercase. Must be unique.
- **`role`**: `pi`, `postdoc`, `phd`, `ms`, `undergrad`, or `visitor`.
- **`start` / `end`**: current students only (`phd`, `ms`, `undergrad`). `start` is a term such as `Fall 2026`. `end` is a term, or the exact string `In progress`. Omit both for faculty. When someone leaves, remove these and add `alumni` instead.
- **`interests`**: up to 5 short phrases.
- **`links`**: include only the ones you want. Also supported: `orcid`, `bluesky`, `twitter`. The People page does not show email addresses. A photo links to `links.website` when that field is set.
- No photo yet? Leave out `photo` and your initials will be shown instead.

**Leaving the lab?** Keep your entry and add an `alumni` object. You'll move to the Alumni section:

```json
"alumni": { "years": "2026–2031", "now": "Research Scientist at Example Corp" }
```

## Add news

Add an object to `data/news.json` (newest items appear first automatically):

```json
{ "date": "2027-05-01", "text": "Our paper on texture bias was accepted to <a href=\"https://www.ieee-security.org/TC/SP2027/\">IEEE S&amp;P 2027</a>!" }
```

- **`date`**: `YYYY-MM-DD`.
- **`text`**: one or two sentences. Links are allowed as `<a href=\"...\">...</a>` (note the `\"` escapes
  inside JSON). Write `&amp;` for a literal `&`.

## Add a lab photo or video

The Photos page (`/photos/`) reads [`data/lab_media.json`](data/lab_media.json).
Every `type: "image"` entry is shown, newest first, in one grid. Videos stay in the catalog and on disk; they are not deleted, and they are not shown. The page says there are no photos when the catalog has no image. Add an item as one object in that array.

Keep optimized photos under 2 MB and videos under 10 MB so the repo does not need Git LFS. The build rejects larger lab files. Do not commit camera originals; they carry GPS and other EXIF.

### Photo

The optimizer reads the original and writes a WebP plus a high-quality JPEG fallback, at most 1600px wide, with EXIF, GPS, and XMP removed. It does not modify the original.

```sh
uv pip install pillow
uv run python scripts/optimize_lab_media.py original.jpg assets/media/lab/2026-12-01/lunch
```

Paste the printed object into `data/lab_media.json`, replace `alt` with what a screen reader should hear, and add `caption` only if you want a visible line:

```json
{
  "id": "2026-12-01-lunch",
  "type": "image",
  "date": "2026-12-01",
  "src": "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/lunch.webp",
  "fallback": "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/lunch.jpg",
  "width": 1600,
  "height": 1200,
  "alt": "Lab members at a table with lunch boxes.",
  "caption": "Friday lunch"
}
```

`src` is the WebP. `fallback` is the JPEG (or PNG) used when a browser has no WebP. `caption` may be omitted.

### Video

Video entries can stay in the catalog. The Photos page does not play them. Transcode to H.264 MP4 when you are keeping a clip on disk. with the moov atom at the front (`+faststart`), a reasonable bitrate, and a file under about 10 MB. Strip metadata so a phone clip does not keep its GPS. Then make a poster with the photo optimizer (that step also strips the poster's metadata).

```sh
ffmpeg -y -i original.mov \
  -map_metadata -1 \
  -vf "scale='min(1280,iw)':-2" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -crf 28 -preset slow -movflags +faststart \
  assets/media/lab/2026-12-01/clip.mp4
ffmpeg -y -ss 00:00:01 -i original.mov -map_metadata -1 -frames:v 1 /tmp/clip-poster.jpg
uv run python scripts/optimize_lab_media.py /tmp/clip-poster.jpg assets/media/lab/2026-12-01/clip-poster
```

The command above keeps the audio track. The People page does not play catalog videos. Add `-an` before the output path when there is no audio worth keeping. If the MP4 cannot stay under 10 MB without falling apart, say so in the pull request instead of committing the camera original.

```json
{
  "id": "2026-12-01-clip",
  "type": "video",
  "date": "2026-12-01",
  "src": "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/clip.mp4",
  "poster": "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/clip-poster.jpg",
  "width": 1280,
  "height": 720,
  "alt": "A short pan across the lab bench.",
  "caption": "Bench tour"
}
```

`poster` is required for a video. The page shows controls and does not autoplay.

## Common validation errors

| Message                                  | Fix                                                        |
|------------------------------------------|------------------------------------------------------------|
| `invalid JSON at line N`                 | Usually a missing or extra comma near line N.              |
| `'x' is not one of [...]`                | Use one of the listed values (e.g. for `role` or `group`). |
| `Additional properties are not allowed`  | A field name is misspelled, or isn't supported.            |
| `duplicate 'x'`                          | Pick a different `key`/`id`.                               |
| `... which does not exist`               | The image URL doesn't match a file you committed.          |

# Contributing to the IRIS Lab website

Almost everything on the site comes from the JSON files in the private
[IRIS-Updates repository](https://github.com/IRIS-Research-Lab/IRIS-Updates/tree/main/data).
Edit content there and add images here. The website generates its public `/data/` files at build time;
do not add content copies to this repository. Please don't edit the HTML/JS unless we've talked about it.

| To change...          | Edit                                   | Images go in                       |
|-----------------------|----------------------------------------|------------------------------------|
| Publications          | [`data/pubs.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/pubs.json)     | `assets/images/publications/`      |
| People                | [`data/people.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/people.json) | `assets/images/people/`            |
| News on the home page | [`data/news.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/news.json)     | —                                  |
| Research themes       | [`data/research.json`](https://github.com/IRIS-Research-Lab/IRIS-Updates/blob/main/data/research.json) | —                              |

> ⚠️ `data/pubs.json` and `data/people.json` are also loaded by Prof. Hoak's personal site (hoak.me).
> **Never rename or delete a publication `key` or person `id`** once it has been merged, and don't move or
> rename the files in `IRIS-Updates/data/`. The public website URLs remain unchanged.

## Workflow

1. In **IRIS-Updates**, create a branch: `git checkout -b add-<something>` (or use GitHub's web editor, which does this for you).
2. Make your edit. Mind the commas: every item in a list is separated by `,` except the last one.
3. Check it locally from your **website checkout** (with IRIS-Updates alongside it):
   ```sh
   pip install "jsonschema[format]"
   python scripts/build.py --data-dir ../IRIS-Updates/data
   ```
4. Preview locally (optional): `python3 -m http.server 8000 --directory _site` from the website repo root, then open
   <http://localhost:8000>.
5. Open a pull request in **IRIS-Updates**. Prof. Hoak (or another lab member) should review it before
   merge. The source merge requests a website build; its validation must pass before publication. If
   it fails, inspect the website Actions log and fix the source. For a new image, merge the image into
   this website repository first, then reference its absolute URL in the source PR. Website code PRs
   retain the **validate** check, which builds against the current public snapshot without private credentials.

## Add a paper

Add an object to `data/pubs.json` (order in the file doesn't matter; the site sorts by year):

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
  are bolded. For equal contribution, add `*` after the names and `"authornote": "* indicates equal contribution"`.
- **`group`**: `conference`, `journal`, `workshop`, `techreport`, `thesis`, or `submission`.
  Papers under review use `submission` and are **not shown** on the site; switch it once accepted.
- **`lab`**: `true` for work done in the IRIS Lab.
- **`image`** (optional): a teaser figure, about 1200px wide, under 1–2 MB. Commit the file to
  `assets/images/publications/` and use the full `https://iris-research-lab.github.io/...` URL.
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
  "photo": "https://iris-research-lab.github.io/assets/images/people/jane-doe.jpg",
  "interests": ["Adversarial robustness", "Vision models"],
  "links": {
    "website": "https://janedoe.github.io",
    "email": "jane.doe@utdallas.edu",
    "scholar": "https://scholar.google.com/citations?user=XXXXXXX",
    "github": "https://github.com/janedoe",
    "linkedin": "https://www.linkedin.com/in/janedoe"
  }
}
```

- **`id`**: `firstname-lastname`, lowercase. Must be unique.
- **`role`**: `pi`, `postdoc`, `phd`, `ms`, `undergrad`, or `visitor`.
- **`interests`**: up to 5 short phrases.
- **`links`**: include only the ones you want. Also supported: `orcid`, `bluesky`, `twitter`.
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

## Common validation errors

| Message                                  | Fix                                                        |
|------------------------------------------|------------------------------------------------------------|
| `invalid JSON at line N`                 | Usually a missing or extra comma near line N.              |
| `'x' is not one of [...]`                | Use one of the listed values (e.g. for `role` or `group`). |
| `Additional properties are not allowed`  | A field name is misspelled, or isn't supported.            |
| `duplicate 'x'`                          | Pick a different `key`/`id`.                               |
| `... which does not exist`               | The image URL doesn't match a file you committed.          |

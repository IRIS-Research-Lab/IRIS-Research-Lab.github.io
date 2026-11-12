"""Exercise shared publication media and visible punctuation without changing data."""
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOTS = "·•‧∙⋅●◦・"


class RenderedHTML(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.links = []
        self.images = []
        self.figures = []
        self.figure = None
        self.in_caption = False
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "figure":
            self.figure = {"images": [], "caption": ""}
            self.figures.append(self.figure)
        elif tag == "figcaption":
            self.in_caption = True
            if self.figure is None:
                raise AssertionError("caption must be inside a figure")
        elif tag == "img":
            self.images.append(attrs)
            if self.figure is not None:
                self.figure["images"].append(attrs)
        elif tag == "a":
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "figcaption":
            self.in_caption = False
        elif tag == "figure":
            self.figure = None

    def handle_data(self, data):
        self.text.append(data)
        if self.in_caption:
            self.figure["caption"] += data


class PresentationTests(unittest.TestCase):
    def run_js(self, script):
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def render(self, expression):
        return self.run_js(
            'globalThis.location = {origin: "http://localhost"};\n'
            'const mod = await import("./assets/js/common.js");\n'
            f'process.stdout.write(JSON.stringify({expression}));')

    def render_pages(self, pubs, people=None, media=None):
        data = dict(pubs=pubs, people=people or [], lab_media=media or [], news=[])
        return self.run_js("""
globalThis.location = {origin: 'http://localhost', hash: ''};
globalThis.addEventListener = () => {};
const data = DATA;
const before = JSON.stringify(data);
globalThis.fetch = async url => ({ok: true, json: async () => data[url.split('/').pop().replace('.json', '')]});
const hosts = {};
globalThis.document = {getElementById(id) { return hosts[id] ||= {innerHTML: '', hidden: true}; }};
await import('./assets/js/home.js');
await import('./assets/js/publications.js');
await import('./assets/js/people.js');
await import('./assets/js/photos.js');
process.stdout.write(JSON.stringify({hosts, unchanged: before === JSON.stringify(data)}));
""".replace("DATA", json.dumps(data)))

    @staticmethod
    def paper(**extra):
        return dict(
            key="synthetic_2025", title="Textures <study> · robustness",
            authors="Blaine Hoak · Ada & Jo", year=2025, group="conference",
            venue="European Conference on Artificial Intelligence (ECAI)",
            image="https://iris-research-lab.github.io/assets/images/publications/fig·1.webp",
            links=[dict(label="Paper · preprint", url="https://example.com/paper·1?a=1&b=2")],
            **extra)

    def test_home_and_research_share_figure_caption_and_feature_selection(self):
        chosen = self.paper()
        pubs = [dict(chosen, key="hidden", title="Hidden", year=2028, show_lab=False),
                dict(chosen, key="thesis", title="Thesis", year=2027, group="thesis"),
                dict(chosen, key="pending", title="Pending", year=2026, group="submission"),
                chosen, dict(chosen, key="second", title="Second source entry")]
        result = self.render_pages(pubs, [dict(id="blaine", name="Blaine Hoak", role="pi")])
        home = RenderedHTML(result["hosts"]["featured-root"]["innerHTML"])
        research = RenderedHTML(result["hosts"]["publications"]["innerHTML"])
        self.assertEqual(len(home.figures), 1)
        self.assertEqual(len(research.figures), 2)
        self.assertEqual(home.figures[0], research.figures[0])
        self.assertEqual(home.figures[0]["caption"],
                         "Figure from this work: European Conference on Artificial Intelligence (ECAI) (2025)")
        self.assertEqual(home.images[0]["src"], "/assets/images/publications/fig·1.webp")
        self.assertEqual(home.images[0]["alt"], "Figure from " + chosen["title"])
        self.assertIn("<strong>Blaine Hoak</strong>", result["hosts"]["publications"]["innerHTML"])
        self.assertTrue(result["unchanged"])

    def test_rendered_copy_has_no_dots_but_links_alt_and_gallery_fallback_survive(self):
        people = [dict(id="blaine", name="Blaine Hoak", role="pi",
                       title="Professor · Computer Science", interests=["Vision · AI", "Security"],
                       photo="https://example.com/person·1.jpg", links=dict(website="https://example.com/me·1")),
                  dict(id="alumnus", name="Ada & Jo", role="phd", alumni=dict(years="2024–2026", now="Industry · research"))]
        media = [dict(id="field", type="image", src="https://example.com/field·1.webp",
                      fallback="https://example.com/field·1.jpg", alt="Field · setup",
                      caption="Field · setup", date="2026-11-03", width=800, height=600)]
        result = self.render_pages([self.paper(authornote="Equal · contribution")], people, media)
        for host in ("featured-root", "publications", "members", "people", "photos"):
            parsed = RenderedHTML(result["hosts"][host]["innerHTML"])
            with self.subTest(host=host):
                self.assertFalse(set("".join(parsed.text)) & set(DOTS))
        gallery = RenderedHTML(result["hosts"]["photos"]["innerHTML"])
        self.assertEqual(gallery.images[0]["src"], media[0]["fallback"])
        self.assertEqual(gallery.images[0]["alt"], media[0]["alt"])
        self.assertEqual(gallery.figures[0]["caption"], "Field, setup, 3 Nov 2026")
        self.assertEqual(gallery.images[0]["width"], "800")
        self.assertEqual(gallery.images[0]["height"], "600")
        home = RenderedHTML(result["hosts"]["featured-root"]["innerHTML"])
        self.assertEqual(home.links, ["https://example.com/paper·1?a=1&b=2"])
        roster = RenderedHTML(result["hosts"]["people"]["innerHTML"])
        self.assertEqual(roster.links, ["https://example.com/me·1"])
        self.assertTrue(result["unchanged"])

    def test_missing_figure_produces_no_empty_figure_or_caption(self):
        result = self.render_pages([dict(self.paper(), image=None)])
        for host in ("featured-root", "publications"):
            markup = result["hosts"][host]["innerHTML"]
            self.assertIn("nofig", markup)
            self.assertFalse(RenderedHTML(markup).figures)

    def test_visible_punctuation_is_escaped_and_decimal_points_stay(self):
        self.assertEqual(self.render('mod.displayText("AI · Security • Vision & <code> at 1.5")'),
                         "AI, Security, Vision &amp; &lt;code&gt; at 1.5")
        self.assertEqual(self.render('mod.presentationText("A‧B∙C⋅D●E◦F・G")'),
                         "A, B, C, D, E, F, G")
        self.assertEqual(self.render('mod.displayText(null)'), "")

    def test_news_normalizes_decoded_text_nodes_without_touching_attributes(self):
        # The browser's TreeWalker supplies only decoded text nodes, including link
        # labels. The adapter checks that the helper uses that boundary, not HTML replacement.
        result = self.run_js("""
const mod = await import('./assets/js/common.js');
const root = {href: 'https://example.com/a·b', alt: 'A · B',
              nodes: [{textContent: 'News · update '}, {textContent: 'Paper • dataset'}]};
globalThis.NodeFilter = {SHOW_TEXT: 4};
globalThis.document = {createTreeWalker(node, kind) {
  if (node !== root || kind !== NodeFilter.SHOW_TEXT) throw Error('text boundary');
  let i = 0;
  return {nextNode: () => node.nodes[i++] || null};
}};
mod.normalizeTextSeparators(root);
process.stdout.write(JSON.stringify(root));
""")
        self.assertEqual(result["nodes"], [{"textContent": "News, update "}, {"textContent": "Paper, dataset"}])
        self.assertEqual(result["href"], "https://example.com/a·b")
        self.assertEqual(result["alt"], "A · B")

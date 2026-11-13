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
            key="synthetic_2025", title="Textures <study> · robustness", highlight=True,
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
        self.assertEqual(len(home.figures), 2)
        self.assertEqual(len(research.figures), 2)
        self.assertEqual(home.figures[0], research.figures[0])
        self.assertEqual(home.figures[0]["caption"],
                         "European Conference on Artificial Intelligence (ECAI) (2025)")
        self.assertEqual(home.images[0]["src"], "/assets/images/publications/fig·1.webp")
        self.assertEqual(home.images[0]["alt"], "Figure from " + chosen["title"])
        self.assertIn("Blaine Hoak", result["hosts"]["publications"]["innerHTML"])
        self.assertNotIn("<strong>Blaine Hoak</strong>", result["hosts"]["publications"]["innerHTML"])
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

    def test_home_features_complete_selection_in_year_then_source_order(self):
        base = self.paper()
        pubs = [dict(base, key='old', title='Older highlighted paper', year=2023),
                dict(base, key='tie-first', title='First 2025 highlight'),
                dict(base, key='unselected', title='Newer unselected paper', year=2029, highlight=False),
                dict(base, key='tie-second', title='Second 2025 highlight'),
                dict(base, key='middle', title='Middle highlighted paper', year=2024),
                dict(base, key='last', title='Last highlighted paper', year=2021, image=None)]
        result = self.render_pages(pubs)
        home = result['hosts']['featured-root']['innerHTML']
        expected = ['First 2025 highlight', 'Second 2025 highlight', 'Middle highlighted paper',
                    'Older highlighted paper', 'Last highlighted paper']
        self.assertEqual(home.count('<article class="pub featured-work'), len(expected))
        self.assertEqual(home.count('id="featured-label"'), 1)
        self.assertEqual(sorted(expected, key=home.index), expected)
        self.assertNotIn('Newer unselected paper', home)
        self.assertEqual(len(RenderedHTML(home).figures), 4)
        self.assertIn('featured-work nofig', home)
        self.assertTrue(result['unchanged'])

    def test_home_highlight_never_overrides_privacy_or_publication_type(self):
        base = self.paper()
        pubs = [dict(base, key='hidden', title='Hidden highlighted paper', show_lab=False, show=True),
                dict(base, key='legacy-hidden', title='Legacy hidden highlight', show=False),
                dict(base, key='thesis', title='Explicit public thesis', group='thesis', show_lab=True),
                dict(base, key='submission', title='Explicit public submission', group='submission', show_lab=True),
                dict(base, key='default-submission', title='Private submission', group='submission'),
                dict(base, key='no-highlight', title='No highlight flag'),
                dict(base, key='false-highlight', title='False highlight', highlight=False)]
        del pubs[-2]['highlight']
        result = self.render_pages(pubs)
        self.assertEqual(result['hosts']['featured-root']['innerHTML'], '')
        research = ''.join(RenderedHTML(result['hosts']['publications']['innerHTML']).text)
        self.assertIn('Explicit public thesis', research)
        self.assertIn('Explicit public submission', research)
        self.assertIn('No highlight flag', research)
        for title in ('Hidden highlighted paper', 'Legacy hidden highlight', 'Private submission'):
            self.assertNotIn(title, research)
        self.assertTrue(result['unchanged'])

    def test_single_home_highlight_preserves_notes_links_and_nofig_fallback(self):
        pub = dict(self.paper(), image=None, authors='Blaine Hoak* and Ada & Jo*',
                   authornote='* indicates equal contribution')
        result = self.render_pages([pub])
        home = result['hosts']['featured-root']['innerHTML']
        parsed = RenderedHTML(home)
        self.assertEqual(home.count('<article class="pub featured-work nofig">'), 1)
        self.assertFalse(parsed.figures)
        self.assertFalse(parsed.images)
        self.assertIn('Blaine Hoak*<strong> and Ada &amp; Jo*</strong>', home)
        self.assertIn('<p class="pub-authornote">* indicates equal contribution</p>', home)
        self.assertEqual(parsed.links, [pub['links'][0]['url']])
        self.assertTrue(result['unchanged'])

    def test_author_emphasis_excludes_pi_in_both_renderers(self):
        class AuthorWeights(HTMLParser):
            def __init__(self, markup):
                super().__init__()
                self.depth = 0
                self.credits = []
                self.feed(markup)

            def handle_starttag(self, tag, attrs):
                if tag == 'strong':
                    self.depth += 1

            def handle_endtag(self, tag):
                if tag == 'strong':
                    self.depth -= 1

            def handle_data(self, text):
                self.credits.append((text, self.depth))

        people = [dict(id='blaine-hoak', name='Blaine Hoak (PI)', role='pi'),
                  dict(id='abhirup-mukherjee', name='Abhirup Mukherjee', role='phd'),
                  dict(id='charles-dardaman', name='Charles Dardaman', role='phd')]
        pub = dict(self.paper(), authors='Blaine Hoak* and Abhirup Mukherjee* and Charles Dardaman and Outside Author')
        result = self.render_pages([pub], people)
        for host in ('featured-root', 'publications'):
            credits = AuthorWeights(result['hosts'][host]['innerHTML']).credits
            with self.subTest(host=host):
                self.assertTrue(any('Blaine Hoak*' in t and d == 0 for t, d in credits))
                self.assertFalse(any('Blaine Hoak' in t and d > 0 for t, d in credits))
                self.assertTrue(any('Abhirup Mukherjee*' in t and d == 1 for t, d in credits))
                self.assertTrue(any('Charles Dardaman' in t and d == 1 for t, d in credits))
                self.assertTrue(any('Outside Author' in t and d == (1 if host == 'featured-root' else 0)
                                    for t, d in credits))
        self.assertTrue(result['unchanged'])

    def test_home_preserves_non_pi_emphasis_and_escaped_source_credit(self):
        authors = "Patrick McDaniel and Blaine Hoak* and A. O'Neil* and Jean & <Jo> and Blaine Hoak"
        pub = dict(self.paper(), authors=authors)
        result = self.render_pages([pub])
        markup = result['hosts']['featured-root']['innerHTML']
        self.assertIn('<strong>Patrick McDaniel and </strong>Blaine Hoak*', markup)
        self.assertIn('<strong> and A. O&#39;Neil* and Jean &amp; &lt;Jo&gt; and </strong>Blaine Hoak', markup)
        self.assertNotIn('<strong>Blaine Hoak', markup)
        self.assertIn(authors, ''.join(RenderedHTML(markup).text))
        self.assertTrue(result['unchanged'])

    def test_explicit_public_thesis_and_submissions_do_not_replace_home_feature(self):
        paper = self.paper()
        pubs = [dict(paper, key='thesis', title='Public thesis', group='thesis', year=2026, show_lab=True),
                dict(paper, key='default-thesis', title='Default thesis', group='thesis', year=2026),
                dict(paper, key='legacy-thesis', title='Legacy thesis', group='thesis', show=True),
                dict(paper, key='public-submission', title='Public submission', group='submission', show_lab=True),
                dict(paper, key='private', title='Unrelated private submission', group='submission'), paper]
        result = self.render_pages(pubs)
        home = ''.join(RenderedHTML(result['hosts']['featured-root']['innerHTML']).text)
        research = ''.join(RenderedHTML(result['hosts']['publications']['innerHTML']).text)
        self.assertIn(paper['title'].replace(' · ', ', '), home)
        self.assertNotIn('Public thesis', home)
        self.assertNotIn('Public submission', home)
        self.assertIn('Public thesis', research)
        self.assertIn('Public submission', research)
        for hidden in ('Default thesis', 'Legacy thesis', 'Unrelated private submission'):
            self.assertNotIn(hidden, research)

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

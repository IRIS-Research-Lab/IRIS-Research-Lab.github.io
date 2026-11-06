// Home: mission is static. Featured work, figured preview, news, and people come from JSON.
import {
  loadJSON, esc, formatDate, photoHTML, roleLine,
  shownOnResearch, byYearThenSource, pubArticleHTML, pubLinksHTML,
  labAuthorHTML, KIND_LABELS, HONESTY_NOTE
} from './common.js';

const [pubs, news, people] = await Promise.all([
  loadJSON('pubs'), loadJSON('news'), loadJSON('people')
]);

const currentPeople = people.filter(person => !person.alumni);
const shown = pubs.filter(shownOnResearch);
const featured = shown.find(pub => pub.research_example && pub.group === 'thesis')
  || shown.find(pub => pub.research_example)
  || shown.find(pub => pub.highlight)
  || shown[0]
  || null;

const root = document.getElementById('featured-root');
if (root && featured) {
  const kind = KIND_LABELS[featured.group] || featured.group;
  // Same switch as Research. Default home shows the featured show:true work only.
  const preview = new URLSearchParams(location.search).get('preview') === 'historical';
  const highlighted = pubs.filter(pub => pub.image && pub.group !== 'submission' && pub.highlight);
  const withImage = highlighted.length
    ? highlighted
    : pubs.filter(pub => pub.image && pub.group !== 'submission');
  const figured = preview ? byYearThenSource(withImage).slice(0, 3) : [];
  const needsNote = figured.some(pub => !shownOnResearch(pub));
  root.innerHTML = `
    <section class="band" id="featured" aria-labelledby="featured-label">
      <h2 class="section-label" id="featured-label">Featured work</h2>
      <p class="kicker featured-kicker">${esc(kind)} · ${esc(featured.year)}</p>
      <h3 class="featured-title">${esc(featured.title)}</h3>
      <p class="featured-meta"><strong>${labAuthorHTML(featured.authors, people)}</strong><br>${esc(featured.venue)} · ${esc(featured.year)}</p>
      ${pubLinksHTML(featured.links)}
      ${figured.length ? `
        <h2 class="section-label spaced" id="figured-label">Works with figures <span class="layout-tag">(layout preview)</span></h2>
        ${needsNote ? HONESTY_NOTE : ''}
        <div aria-labelledby="figured-label">${figured.map(pub => pubArticleHTML(pub, people)).join('')}</div>
      ` : ''}
    </section>`;
}

const newsItems = news.slice().sort((a, b) => b.date.localeCompare(a.date));
const newsSection = document.getElementById('news-section');
const newsList = document.getElementById('news-list');
if (newsSection && newsList && newsItems.length) {
  newsSection.hidden = false;
  // News text may contain simple HTML links (reviewed in the source repo).
  newsList.innerHTML = newsItems.map(item => `
    <article class="news-item">
      <time datetime="${esc(item.date)}">${formatDate(item.date)}</time>
      <p class="news-body">${item.text}</p>
    </article>`).join('');
}

const members = document.getElementById('members');
if (members) {
  members.innerHTML = currentPeople.map(person => `
    <div class="person" id="home-${esc(person.id)}">
      ${photoHTML(person, 'person-photo')}
      <div>
        <h3>${esc(person.name)}</h3>
        <div class="role">${esc(roleLine(person))}</div>
      </div>
    </div>`).join('');
}

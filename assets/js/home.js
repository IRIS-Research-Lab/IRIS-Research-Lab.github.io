// Home: the group bio is static in index.html. Featured work, news, and people come from JSON.
import {
  loadJSON, esc, formatDate, photoHTML, roleLine,
  shownOnResearch, byYearThenSource, pubLinksHTML,
  labAuthorHTML, KIND_LABELS
} from './common.js';

const [pubs, news, people] = await Promise.all([
  loadJSON('pubs'), loadJSON('news'), loadJSON('people')
]);

const currentPeople = people.filter(person => !person.alumni);
// Newest published paper: year descending, then the order in pubs.json.
const featured = byYearThenSource(
  pubs.filter(pub => shownOnResearch(pub) && pub.group !== 'submission')
)[0] || null;

const root = document.getElementById('featured-root');
if (root && featured) {
  const kind = KIND_LABELS[featured.group] || featured.group;
  root.innerHTML = `
    <section class="band" id="featured" aria-labelledby="featured-label">
      <h2 class="section-label" id="featured-label">Featured work</h2>
      <p class="kicker featured-kicker">${esc(kind)} · ${esc(featured.year)}</p>
      <h3 class="featured-title">${esc(featured.title)}</h3>
      <p class="featured-meta"><strong>${labAuthorHTML(featured.authors, people)}</strong><br>${esc(featured.venue)} · ${esc(featured.year)}</p>
      ${pubLinksHTML(featured.links)}
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

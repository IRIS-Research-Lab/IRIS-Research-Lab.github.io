// Home: the group bio is static in index.html. Featured work, news, and people come from JSON.
import {
  loadJSON, esc, displayText, normalizeTextSeparators, formatDate, photoHTML, roleLine,
  shownOnResearch, byYearThenSource, pubLinksHTML,
  featuredAuthorHTML, pubFigureHTML, KIND_LABELS
} from './common.js';

const [pubs, news, people] = await Promise.all([
  loadJSON('pubs'), loadJSON('news'), loadJSON('people')
]);

const currentPeople = people.filter(person => !person.alumni);
// All highlighted published papers: year descending, then the order in pubs.json.
// Highlight selection never overrides lab-site visibility or publishes submissions/theses.
const featured = byYearThenSource(
  pubs.filter(pub => pub.highlight === true && shownOnResearch(pub)
    && !['submission', 'thesis'].includes(pub.group))
);

const root = document.getElementById('featured-root');
if (root && featured.length) {
  root.innerHTML = `
    <section class="band" id="featured" aria-labelledby="featured-label">
      <h2 class="section-label" id="featured-label">Featured work</h2>
      <div class="home-sections">
      ${featured.map(pub => `
      <article class="pub featured-work${pub.image ? '' : ' nofig'}">
        <div class="pub-cite">
          <p class="kicker featured-kicker">${displayText(KIND_LABELS[pub.group] || pub.group)}, ${displayText(pub.year)}</p>
          <h3 class="featured-title">${displayText(pub.title)}</h3>
          <p class="featured-meta">${featuredAuthorHTML(pub.authors)}<br>${displayText(pub.venue)} (${displayText(pub.year)})</p>
          ${pub.authornote ? `<p class="pub-authornote">${displayText(pub.authornote)}</p>` : ''}
          ${pubLinksHTML(pub.links)}
        </div>
        ${pubFigureHTML(pub)}
      </article>`).join('')}
      </div>
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
  normalizeTextSeparators(newsList);
}

const members = document.getElementById('members');
if (members) {
  members.innerHTML = currentPeople.map(person => `
    <div class="person" id="home-${esc(person.id)}">
      ${photoHTML(person, 'person-photo')}
      <div>
        <h3>${displayText(person.name)}</h3>
        <div class="role">${displayText(roleLine(person))}</div>
      </div>
    </div>`).join('');
}

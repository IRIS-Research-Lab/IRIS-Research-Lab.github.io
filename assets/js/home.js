// assets/js/home.js — research themes, news, and member strip on the home page.
import { loadJSON, esc, formatDate, photoHTML } from './common.js';

const [themes, news, people] = await Promise.all([
  loadJSON('research'), loadJSON('news'), loadJSON('people')
]);

document.getElementById('themes').innerHTML = themes.map(t => `
  <div class="col-md-4">
    <a class="iris-card d-block h-100" href="/research/#${esc(t.id)}">
      <div class="theme-icon"><i class="${esc(t.icon || 'fa-solid fa-flask')}"></i></div>
      <h3 class="h5"><span class="theme-letter">${esc(t.title[0])}</span>${esc(t.title.slice(1))}</h3>
      <p class="mb-0 text-body-secondary small">${esc(t.summary)}</p>
    </a>
  </div>`).join('');

// News text may contain simple HTML links (reviewed in PRs), so it is not escaped.
document.getElementById('news-list').innerHTML = news
  .slice()
  .sort((a, b) => b.date.localeCompare(a.date))
  .map(n => `<li><span class="news-date">${formatDate(n.date)}</span><span>${n.text}</span></li>`)
  .join('');

document.getElementById('members').innerHTML = people
  .filter(p => !p.alumni)
  .map(p => {
    const profile = `/people/#${esc(p.id)}`;
    if (!p.website) {
      return `<a href="${profile}">${photoHTML(p, '')}<div>${esc(p.name)}</div></a>`;
    }
    // The photo link cannot sit inside the profile link.
    return `<div class="member">${photoHTML(p, '')}<a class="member-name" href="${profile}">${esc(p.name)}</a></div>`;
  })
  .join('');

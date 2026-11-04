// Research publications. `show` decides what is listed; a missing flag hides years before 2026.
import { loadJSON, esc, asset, linkButtonHTML } from './common.js';

const container = document.getElementById('publications');

try {
  const [pubs, people] = await Promise.all([loadJSON('pubs'), loadJSON('people')]);

  // Bold every lab member's name in author lists (ignoring nicknames in parentheses).
  const escapeRegExp = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const namePatterns = people.map(p => {
    const name = esc(p.name.replace(/\s*\(.*?\)/g, '').trim());
    return new RegExp(`\\b${escapeRegExp(name)}\\b\\*?`, 'g');
  });
  function formatAuthors(authors) {
    let html = esc(authors);
    for (const re of namePatterns) html = html.replace(re, m => `<strong>${m}</strong>`);
    return html;
  }

  function pubHTML(p) {
    return `
      <article class="iris-card pub mb-3" id="${esc(p.key)}">
        ${p.image ? `<img class="pub-img" src="${esc(asset(p.image))}" alt="${esc(p.title)}" loading="lazy" width="240" height="160">` : ''}
        <div class="flex-grow-1">
          <h3 class="pub-title">${esc(p.title)}</h3>
          ${p.award ? `<span class="badge-award me-1">🏆 ${esc(p.award)}</span>` : ''}
          ${p.talkbadge ? `<span class="badge-talk">🎤 ${esc(p.talkbadge)}</span>` : ''}
          <div class="pub-authors">${formatAuthors(p.authors)}</div>
          ${p.authornote ? `<div class="pub-authors small fst-italic">${esc(p.authornote)}</div>` : ''}
          <div class="pub-venue">${esc(p.venue)}, ${p.year}</div>
          <div class="d-flex flex-wrap gap-2">${(p.links || []).map(linkButtonHTML).join('')}</div>
        </div>
      </article>`;
  }

  // `show` is the display source of truth. An omitted flag hides work from
  // before 2026 and otherwise keeps the lab / research-example / non-submission rule.
  function shownOnResearch(p) {
    if (p.show === true) return true;
    if (p.show === false) return false;
    return p.year >= 2026 && (p.lab === true || p.research_example === true) && p.group !== 'submission';
  }

  const shown = pubs.filter(shownOnResearch);
  if (!shown.length) {
    container.innerHTML = `
      <div class="iris-card empty-state">
        <i class="fa-solid fa-hourglass-half d-block"></i>
        <h2 class="h5">Our first publications are on the way</h2>
        <p class="mb-0">The IRIS Lab launched in Fall 2026, so check back soon.
          In the meantime, see Prof. Hoak's <a href="https://www.hoak.me/research/publications/">prior publications</a>.</p>
      </div>`;
  } else {
    const years = [...new Set(shown.map(p => p.year))].sort((a, b) => b - a);
    container.innerHTML = years.map(y =>
      `<h2 class="year-heading">${y}</h2>` + shown.filter(p => p.year === y).map(pubHTML).join('')
    ).join('');
  }

  function revealPaper() {
    const paper = shown.find(p => `#${p.key}` === location.hash);
    if (paper) document.getElementById(paper.key)?.scrollIntoView();
  }
  revealPaper();
  addEventListener('hashchange', revealPaper);
} catch {
  container.innerHTML = '<p role="alert">Publications could not be loaded. Please try again later.</p>';
}

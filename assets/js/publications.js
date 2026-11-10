// Research publications. `show` decides the live list. Theses are never listed.
import {
  loadJSON, esc, pubArticleHTML, shownOnResearch, byYearThenSource
} from './common.js';

const container = document.getElementById('publications');
if (!container) {
  // Loaded only where the list exists. Home does not mount this script.
} else {
  try {
    const [pubs, people] = await Promise.all([loadJSON('pubs'), loadJSON('people')]);
    const ordered = byYearThenSource(pubs.filter(shownOnResearch));

    if (!ordered.length) {
      container.innerHTML = `
        <p class="empty">The IRIS Lab launched in Fall 2026, so check back soon.
          In the meantime, see Prof. Hoak's <a href="https://www.hoak.me/research/publications/">prior publications</a>.</p>`;
    } else {
      const groups = [];
      for (const pub of ordered) {
        const last = groups[groups.length - 1];
        if (!last || last.year !== pub.year) groups.push({ year: pub.year, pubs: [pub] });
        else last.pubs.push(pub);
      }
      container.innerHTML = groups.map(group => `
        <section class="pub-year">
          <h2 class="section-label">${esc(group.year)}</h2>
          <ol class="pub-list">${group.pubs.map(pub =>
            `<li>${pubArticleHTML(pub, people)}</li>`
          ).join('')}</ol>
        </section>`).join('');
    }

    function revealPaper() {
      const paper = ordered.find(pub => `#${pub.key}` === location.hash);
      if (paper) document.getElementById(paper.key)?.scrollIntoView();
    }
    revealPaper();
    addEventListener('hashchange', revealPaper);
  } catch {
    container.innerHTML = '<p class="empty" role="alert">Publications could not be loaded. Please try again later.</p>';
  }
}

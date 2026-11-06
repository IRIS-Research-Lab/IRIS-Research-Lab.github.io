// Research publications. `show` decides the live list. ?preview=historical is layout-only.
import {
  loadJSON, pubArticleHTML, shownOnResearch, byYearThenSource, HONESTY_NOTE
} from './common.js';

const container = document.getElementById('publications');
if (!container) {
  // Loaded only where the list exists. Home does not mount this script.
} else {
  const note = document.getElementById('honesty-note');
  const preview = new URLSearchParams(location.search).get('preview') === 'historical';

  try {
    const [pubs, people] = await Promise.all([loadJSON('pubs'), loadJSON('people')]);
    const visible = preview
      ? pubs.filter(pub => pub.group !== 'submission')
      : pubs.filter(shownOnResearch);
    const ordered = byYearThenSource(visible);
    const historical = ordered.some(pub => !shownOnResearch(pub));

    if (note) note.innerHTML = historical ? HONESTY_NOTE : '';

    if (!ordered.length) {
      container.innerHTML = `
        <p class="empty">The IRIS Lab launched in Fall 2026, so check back soon.
          In the meantime, see Prof. Hoak's <a href="https://www.hoak.me/research/publications/">prior publications</a>.</p>`;
    } else {
      container.innerHTML = `<ol class="pub-list">${ordered.map(pub =>
        `<li>${pubArticleHTML(pub, people)}</li>`
      ).join('')}</ol>`;
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

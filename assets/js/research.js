// assets/js/research.js — renders research themes from data/research.json.
import { loadJSON, esc } from './common.js';

const themes = await loadJSON('research');
document.getElementById('themes').innerHTML = themes.map(t => `
  <div class="iris-card mb-4" id="${esc(t.id)}">
    <div class="d-flex gap-3 align-items-start">
      <div class="theme-icon flex-shrink-0 mb-0"><i class="${esc(t.icon || 'fa-solid fa-flask')}"></i></div>
      <div>
        <h2 class="h4 mb-2"><span class="theme-letter">${esc(t.title[0])}</span>${esc(t.title.slice(1))}</h2>
        <p class="mb-0">${esc(t.summary)}</p>
      </div>
    </div>
  </div>`).join('');

if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();

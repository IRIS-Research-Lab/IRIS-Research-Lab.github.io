// Publications are the primary Research content; keep source-owned themes compact.
import './publications.js';
import { loadJSON, esc } from './common.js';

try {
  const themes = await loadJSON('research');
  document.getElementById('themes').innerHTML = themes.map(t => `
    <details id="${esc(t.id)}" class="research-topic">
      <summary>${esc(t.title)}</summary>
      <p class="text-muted small mt-2 mb-0">${esc(t.summary)}</p>
    </details>`).join('');
  function revealTheme() {
    const theme = themes.find(t => `#${t.id}` === location.hash);
    if (theme) {
      const el = document.getElementById(theme.id);
      el.open = true;
      el.scrollIntoView();
    }
  }
  revealTheme();
  addEventListener('hashchange', revealTheme);
} catch {
  document.querySelector('.research-focus').hidden = true;
}

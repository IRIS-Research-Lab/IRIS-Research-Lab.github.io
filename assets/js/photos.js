// Lab photos from data/lab_media.json. Every image is shown. Videos stay in the catalog.
import { loadJSON, esc, asset, formatDate } from './common.js';

function caption(item) {
  const parts = [];
  if (item.caption) parts.push(item.caption);
  if (item.date) parts.push(formatDate(item.date));
  return parts.join(' · ');
}

function figure(item) {
  const size = Number.isInteger(item.width) && Number.isInteger(item.height)
    ? ` width="${item.width}" height="${item.height}"` : '';
  const img = item.fallback
    ? `<picture><source srcset="${esc(asset(item.src))}" type="image/webp"><img src="${esc(asset(item.fallback))}" alt="${esc(item.alt)}"${size} loading="lazy" decoding="async"></picture>`
    : `<img src="${esc(asset(item.src))}" alt="${esc(item.alt)}"${size} loading="lazy" decoding="async">`;
  const line = caption(item);
  return `<li><figure>${img}${line ? `<figcaption>${esc(line)}</figcaption>` : ''}</figure></li>`;
}

const host = document.getElementById('photos');
try {
  const media = await loadJSON('lab_media');
  const images = (Array.isArray(media) ? media : []).filter(item => item && item.type === 'image' && item.src);
  images.sort((a, b) => (b.date || '').localeCompare(a.date || '') || String(a.id).localeCompare(String(b.id)));
  host.innerHTML = images.length
    ? `<ul class="photo-grid">${images.map(figure).join('')}</ul>`
    : '<p class="empty">No photos yet.</p>';
} catch {
  host.innerHTML = '<p class="empty">Photos could not be loaded.</p>';
}

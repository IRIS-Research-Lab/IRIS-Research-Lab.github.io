// People roster from data/people.json. Photos use each person's website field.
// Lab media: show one photo. Other catalog entries stay on disk and are not deleted.
import { loadJSON, esc, asset, photoHTML, roleLine, formatDate } from './common.js';

function datesHTML(person) {
  const start = typeof person.start === 'string' ? person.start.trim() : '';
  const end = typeof person.end === 'string' ? person.end.trim() : '';
  if (!start || !end) return '';
  return `<p class="dates">${esc(start)} \u2013 ${esc(end)}</p>`;
}

function memberHTML(person) {
  const interests = (person.interests || []).filter(Boolean);
  return `
    <li class="member" id="${esc(person.id)}">
      ${photoHTML(person)}
      <h2>${esc(person.name)}</h2>
      <p class="role">${esc(roleLine(person))}</p>
      ${datesHTML(person)}
      ${interests.length ? `<p class="interests">${interests.map(item => esc(item)).join(' · ')}</p>` : ''}
    </li>`;
}

function roster(people) {
  if (!people.length) return '';
  return `<ul class="roster">${people.map(memberHTML).join('')}</ul>`;
}

const people = await loadJSON('people');
const current = people.filter(person => !person.alumni);
const alumni = people.filter(person => person.alumni);
const host = document.getElementById('people');
host.innerHTML = roster(current) + (alumni.length
  ? `<h2 class="section-label">Alumni</h2>${roster(alumni)}`
  : '');

function labCaption(item) {
  const parts = ['Around the lab'];
  if (item.caption) parts.push(item.caption);
  if (item.date) parts.push(formatDate(item.date));
  parts.push('IRIS Lab');
  return parts.join(' · ');
}

function oneLabPhoto(media) {
  const images = (Array.isArray(media) ? media : []).filter(item => item && item.type === 'image' && item.src);
  images.sort((a, b) => (b.date || '').localeCompare(a.date || '') || String(a.id).localeCompare(String(b.id)));
  return images[0] || null;
}

function renderLabPhoto(item) {
  const slot = document.getElementById('photos');
  if (!slot || !item) return;
  const size = Number.isInteger(item.width) && Number.isInteger(item.height)
    ? ` width="${item.width}" height="${item.height}"` : '';
  const img = item.fallback
    ? `<picture><source srcset="${esc(asset(item.src))}" type="image/webp"><img src="${esc(asset(item.fallback))}" alt="${esc(item.alt)}"${size} loading="lazy" decoding="async"></picture>`
    : `<img src="${esc(asset(item.src))}" alt="${esc(item.alt)}"${size} loading="lazy" decoding="async">`;
  slot.hidden = false;
  slot.innerHTML = `
    <h2 class="section-label" id="photos-title">Photos &amp; fun</h2>
    <figure>${img}<figcaption>${esc(labCaption(item))}</figcaption></figure>`;
}

try {
  renderLabPhoto(oneLabPhoto(await loadJSON('lab_media')));
} catch {
  // The roster still renders when the gallery catalog is missing.
}

if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();

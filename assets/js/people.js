// assets/js/people.js — renders Photos & fun, then data/people.json grouped by role.
import { loadJSON, esc, asset, photoHTML, formatDate, ROLE_LABELS } from './common.js';

const SECTIONS = [
  { title: 'Faculty', roles: ['pi'] },
  { title: 'Postdocs', roles: ['postdoc'] },
  { title: 'PhD Students', roles: ['phd'] },
  { title: "Master's Students", roles: ['ms'] },
  { title: 'Undergraduate Researchers', roles: ['undergrad'] },
  { title: 'Visitors', roles: ['visitor'] }
];

const LINKS = [
  ['website', 'fa-solid fa-globe', 'Website'],
  ['email', 'fa-solid fa-envelope', 'Email'],
  ['scholar', 'fa-brands fa-google-scholar', 'Google Scholar'],
  ['github', 'fa-brands fa-github', 'GitHub'],
  ['linkedin', 'fa-brands fa-linkedin', 'LinkedIn'],
  ['orcid', 'fa-brands fa-orcid', 'ORCID'],
  ['bluesky', 'fa-brands fa-bluesky', 'Bluesky'],
  ['twitter', 'fa-brands fa-x-twitter', 'X']
];

function card(p) {
  const links = LINKS
    .filter(([k]) => p.links?.[k])
    .map(([k, icon, label]) => {
      const href = k === 'email' ? `mailto:${p.links[k]}` : p.links[k];
      return `<a href="${esc(href)}" aria-label="${label}" title="${label}" target="_blank" rel="noopener"><i class="${icon}"></i></a>`;
    }).join('');
  const subtitle = p.alumni
    ? `${ROLE_LABELS[p.role]}, ${esc(p.alumni.years)}${p.alumni.now ? `<br>Now: ${esc(p.alumni.now)}` : ''}`
    : esc(p.title || ROLE_LABELS[p.role]);
  return `
    <div class="col-sm-6 col-lg-4" id="${esc(p.id)}">
      <div class="iris-card person-card h-100">
        ${photoHTML(p)}
        <h3 class="h5 mb-1">${esc(p.name)}</h3>
        <div class="person-role">${subtitle}</div>
        <div>${(p.interests || []).map(i => `<span class="tag">${esc(i)}</span>`).join('')}</div>
        ${links ? `<div class="person-links">${links}</div>` : ''}
      </div>
    </div>`;
}

function section(title, people) {
  if (!people.length) return '';
  return `<h2 class="section-title">${title}</h2><div class="row g-4 mb-5">${people.map(card).join('')}</div>`;
}

const people = await loadJSON('people');
const current = people.filter(p => !p.alumni);
const alumni = people.filter(p => p.alumni);

document.getElementById('people').innerHTML =
  SECTIONS.map(s => section(s.title, current.filter(p => s.roles.includes(p.role)))).join('') +
  section('Alumni', alumni);

function dimensions(item) {
  if (!Number.isInteger(item.width) || !Number.isInteger(item.height)) return '';
  return ` width="${item.width}" height="${item.height}"`;
}

function captionHTML(item) {
  const parts = [];
  if (item.date) parts.push(`<time datetime="${esc(item.date)}">${esc(formatDate(item.date))}</time>`);
  if (item.caption) parts.push(esc(item.caption));
  if (!parts.length) return '';
  return `<figcaption class="lab-media-caption">${parts.join('<span class="lab-media-dot" aria-hidden="true">·</span>')}</figcaption>`;
}

function mediaHTML(item) {
  const size = dimensions(item);
  let visual;
  if (item.type === 'video') {
    const poster = item.poster ? ` poster="${esc(asset(item.poster))}"` : '';
    visual = `<video class="lab-media-visual" controls muted playsinline preload="metadata" loading="lazy"${poster}${size} aria-label="${esc(item.alt)}">` +
      `<source src="${esc(asset(item.src))}" type="video/mp4"></video>`;
  } else if (item.fallback) {
    visual = `<picture><source srcset="${esc(asset(item.src))}" type="image/webp">` +
      `<img class="lab-media-visual" src="${esc(asset(item.fallback))}" alt="${esc(item.alt)}"${size} loading="lazy" decoding="async"></picture>`;
  } else {
    visual = `<img class="lab-media-visual" src="${esc(asset(item.src))}" alt="${esc(item.alt)}"${size} loading="lazy" decoding="async">`;
  }
  return `<figure class="lab-media-card">${visual}${captionHTML(item)}</figure>`;
}

function renderLabMedia(media) {
  const host = document.getElementById('photos');
  if (!host || !Array.isArray(media) || !media.length) return;
  const items = [...media].sort((a, b) => (b.date || '').localeCompare(a.date || '') || String(a.id).localeCompare(String(b.id)));
  host.hidden = false;
  host.setAttribute('aria-labelledby', 'photos-title');
  host.innerHTML = `<h2 class="section-title" id="photos-title">Photos &amp; fun</h2>` +
    `<div class="lab-gallery">${items.map(mediaHTML).join('')}</div>`;
}

const media = await loadJSON('lab_media');
renderLabMedia(media);

// Scroll to #id after rendering (the target didn't exist when the page loaded).
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();

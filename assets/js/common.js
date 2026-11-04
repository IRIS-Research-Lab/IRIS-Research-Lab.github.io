// assets/js/common.js — shared helpers for every page.

export const SITE = 'https://iris-research-lab.github.io';

// Data files store absolute URLs (so hoak.me can use them too). When previewing
// locally, rewrite this site's URLs to relative paths so new images show up
// before they are pushed.
export function asset(url) {
  if (url && location.origin !== SITE && url.startsWith(SITE + '/')) {
    return url.slice(SITE.length);
  }
  return url;
}

export async function loadJSON(name) {
  const res = await fetch(`/data/${name}.json`);
  if (!res.ok) throw new Error(`Could not load data/${name}.json (${res.status})`);
  return res.json();
}

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);
}

export function formatDate(iso) {
  // Parse YYYY-MM-DD as a local date so it doesn't shift a day in US timezones.
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function initials(name) {
  return name.replace(/\(.*?\)/g, '').trim().split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

const PHOTO_POSITION = /^(?:left|center|right|0%|[1-9]\d?%|100%) (?:top|center|bottom|0%|[1-9]\d?%|100%)$/;

function photoPositionStyle(person) {
  const value = typeof person.photoPosition === 'string' ? person.photoPosition.trim() : '';
  return PHOTO_POSITION.test(value) ? ` style="object-position: ${value}"` : '';
}

export function photoHTML(person, cls = 'person-photo') {
  const linked = Boolean(person.website);
  const visual = person.photo
    ? `<img class="${cls}" src="${esc(asset(person.photo))}" alt="${linked ? '' : esc(person.name)}" loading="lazy"${photoPositionStyle(person)}>`
    : `<span class="${cls} person-photo-placeholder" aria-hidden="true">${esc(initials(person.name))}</span>`;
  if (!linked) return visual;
  return `<a class="person-photo-link" href="${esc(person.website)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(person.name)}'s website">${visual}</a>`;
}

export const ROLE_LABELS = {
  pi: 'Principal Investigator',
  postdoc: 'Postdoctoral Researcher',
  phd: 'PhD Student',
  ms: "Master's Student",
  undergrad: 'Undergraduate Researcher',
  visitor: 'Visiting Researcher'
};

const LINK_ICONS = {
  paper: 'fa-solid fa-file-lines',
  code: 'fa-brands fa-github',
  dataset: 'fa-solid fa-database',
  poster: 'fa-solid fa-image',
  slides: 'fa-solid fa-file-powerpoint',
  talk: 'fa-solid fa-video',
  recording: 'fa-solid fa-video',
  youtube: 'fa-brands fa-youtube',
  blog: 'fa-brands fa-medium',
  article: 'fa-solid fa-newspaper',
  website: 'fa-solid fa-globe'
};

export function linkIcon(label) {
  const l = label.toLowerCase();
  const key = Object.keys(LINK_ICONS).find(k => l.includes(k));
  return key ? LINK_ICONS[key] : 'fa-solid fa-link';
}

export function linkButtonHTML(link) {
  return `<a class="btn-link-pill" href="${esc(asset(link.url))}" target="_blank" rel="noopener">` +
    `<i class="${linkIcon(link.label)}"></i>${esc(link.label)}</a>`;
}

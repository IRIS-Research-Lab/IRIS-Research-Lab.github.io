// assets/js/common.js — shared helpers for every page.

export const SITE = 'https://iris-research-lab.github.io';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export const KIND_LABELS = {
  thesis: 'PhD thesis',
  conference: 'Conference paper',
  workshop: 'Workshop paper',
  journal: 'Journal article',
  techreport: 'Technical report',
  submission: 'Submission'
};

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
  const [y, m, d] = String(iso).split('-').map(Number);
  if (!y || !m || !d) return esc(iso);
  return `${d} ${MONTHS[m - 1]} ${y}`;
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
  const site = person.links?.website || '';
  const visual = person.photo
    ? `<img class="${cls}" src="${esc(asset(person.photo))}" alt="${esc(person.name)}" loading="lazy"${photoPositionStyle(person)}>`
    : `<span class="${cls} person-photo-placeholder" aria-hidden="true">${esc(initials(person.name))}</span>`;
  if (!site) return visual;
  // The website field is the photo's destination. Do not also print that URL as text.
  // A photo's alt names the link. Initials are aria-hidden, so that link needs its own name.
  const label = person.photo ? '' : ` aria-label="${esc(`Website for ${person.name}`)}"`;
  return `<a class="person-photo-link" href="${esc(site)}"${label}>${visual}</a>`;
}

export const ROLE_LABELS = {
  pi: 'Principal Investigator',
  postdoc: 'Postdoctoral Researcher',
  phd: 'PhD Student',
  ms: "Master's Student",
  undergrad: 'Undergraduate Researcher',
  visitor: 'Visiting Researcher'
};

export function roleLine(person) {
  if (person.alumni) {
    const base = `${ROLE_LABELS[person.role] || person.role}, ${person.alumni.years}`;
    return person.alumni.now ? `${base} · Now ${person.alumni.now}` : base;
  }
  if (person.role === 'pi') return `PI · ${person.title || ROLE_LABELS.pi}`;
  if (person.role === 'phd') return person.title || 'PhD Student';
  return person.title || ROLE_LABELS[person.role] || person.role;
}

// `show_lab` lists or hides an entry on the lab site. A thesis is never listed.
// An omitted flag lists published work and hides under-review submissions.
// Year is not a display rule. The personal site does not read this field.
export function shownOnResearch(pub) {
  if (pub.group === 'thesis') return false;
  if (pub.show_lab === false) return false;
  if (pub.show_lab === true) return true;
  return pub.group !== 'submission';
}

export function byYearThenSource(pubs) {
  return pubs
    .map((pub, index) => ({ pub, index }))
    .sort((a, b) => b.pub.year - a.pub.year || a.index - b.index)
    .map(item => item.pub);
}

export function labAuthorHTML(authors, people) {
  let html = esc(authors);
  const escapeRegExp = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  for (const person of people || []) {
    const name = String(person.name || '').replace(/\s*\(.*?\)/g, '').trim();
    if (!name) continue;
    // Match the escaped author string, so names with ', &, or < still bold.
    const re = new RegExp(`\\b${escapeRegExp(esc(name))}\\b\\*?`, 'g');
    html = html.replace(re, match => `<strong>${match}</strong>`);
  }
  return html;
}

export function pubLinksHTML(links) {
  const items = (links || []).filter(link => link && link.label && link.url);
  if (!items.length) return '';
  const anchors = items.map(link =>
    `<a href="${esc(asset(link.url))}">${esc(link.label)}</a>`
  );
  return `<p class="pub-links">${anchors.join('<span class="pub-dot" aria-hidden="true"> · </span>')}</p>`;
}

export function pubArticleHTML(pub, people) {
  const kind = KIND_LABELS[pub.group] || pub.group || '';
  const figure = pub.image ? `
    <figure class="pub-fig">
      <img src="${esc(asset(pub.image))}" alt="${esc(`Figure from ${pub.title}`)}" loading="lazy">
      <figcaption>Figure from this work · ${esc(pub.venue)} (${esc(pub.year)})</figcaption>
    </figure>` : '';
  return `
    <article class="pub${pub.image ? '' : ' nofig'}" id="${esc(pub.key)}">
      <div class="pub-cite">
        <p class="pub-tags"><span class="kind">${esc(kind)}</span><span class="year-tag">${esc(pub.year)}</span></p>
        <h3 class="pub-title">${esc(pub.title)}</h3>
        <p class="pub-authors">${labAuthorHTML(pub.authors, people)}</p>
        ${pub.authornote ? `<p class="pub-authornote">${esc(pub.authornote)}</p>` : ''}
        <p class="pub-venue">${esc(pub.venue)} · ${esc(pub.year)}</p>
        ${pubLinksHTML(pub.links)}
      </div>
      ${figure}
    </article>`;
}

// assets/js/people.js — renders data/people.json grouped by role.
import { loadJSON, esc, photoHTML, ROLE_LABELS } from './common.js';

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

// Scroll to #id after rendering (the target didn't exist when the page loaded).
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();

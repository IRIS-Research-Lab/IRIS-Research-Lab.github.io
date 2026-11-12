// People roster from data/people.json. Photos use each person's website field.
// Lab photos live on /photos/.
import { loadJSON, esc, displayText, photoHTML, roleLine } from './common.js';

function datesHTML(person) {
  const start = typeof person.start === 'string' ? person.start.trim() : '';
  const end = typeof person.end === 'string' ? person.end.trim() : '';
  if (!start || !end) return '';
  return `<p class="dates">${displayText(start)} \u2013 ${displayText(end)}</p>`;
}

function memberHTML(person) {
  const interests = (person.interests || []).filter(Boolean);
  return `
    <li class="member" id="${esc(person.id)}">
      ${photoHTML(person)}
      <h2>${displayText(person.name)}</h2>
      <p class="role">${displayText(roleLine(person))}</p>
      ${datesHTML(person)}
      ${interests.length ? `<p class="interests">${interests.map(item => displayText(item)).join('; ')}</p>` : ''}
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

if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();

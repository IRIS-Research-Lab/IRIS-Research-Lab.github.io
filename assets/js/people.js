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
  return `
    <li class="member" id="${esc(person.id)}">
      ${photoHTML(person)}
      <h3>${displayText(person.name)}</h3>
      <p class="role">${displayText(roleLine(person))}</p>
      ${datesHTML(person)}
    </li>`;
}

// Section order on the page. Groups with no members are skipped, so a new
// section (e.g. Master's Students) appears as soon as someone has that role.
const GROUPS = [
  { label: 'Principal Investigator', match: p => !p.alumni && p.role === 'pi' },
  { label: 'Postdoctoral Researchers', match: p => !p.alumni && p.role === 'postdoc' },
  { label: 'PhD Students', match: p => !p.alumni && p.role === 'phd' },
  { label: "Master's Students", match: p => !p.alumni && p.role === 'ms' },
  { label: 'Undergraduate Researchers', match: p => !p.alumni && p.role === 'undergrad' },
  { label: 'Visiting Researchers', match: p => !p.alumni && p.role === 'visitor' },
  { label: 'Alumni', match: p => Boolean(p.alumni) }
];

function section({ label }, people) {
  if (!people.length) return '';
  return `
    <section class="roster-group">
      <h2 class="section-label">${esc(label)}</h2>
      <ul class="roster">${people.map(memberHTML).join('')}</ul>
    </section>`;
}

const people = await loadJSON('people');
document.getElementById('people').innerHTML = GROUPS
  .map(group => section(group, people.filter(group.match)))
  .join('');

if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();

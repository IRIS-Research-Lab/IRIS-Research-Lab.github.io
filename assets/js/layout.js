// assets/js/layout.js — injects the shared header and footer, and marks the current page.
async function inject(id, url) {
  const el = document.getElementById(id);
  if (!el) return;
  const res = await fetch(url);
  el.outerHTML = await res.text();
}

await Promise.all([
  inject('navbar-placeholder', '/partials/navbar.html'),
  inject('footer-placeholder', '/partials/footer.html')
]);

// Compare first path segments: "/people/" -> "people", "/" or "/index.html" -> "".
const segment = path => path.split('/')[1].replace(/^index\.html$/, '');
const current = segment(location.pathname);
document.querySelectorAll('.site-nav .nav-link').forEach(a => {
  if (segment(new URL(a.href).pathname) === current) {
    a.classList.add('active');
    a.setAttribute('aria-current', 'page');
  }
});

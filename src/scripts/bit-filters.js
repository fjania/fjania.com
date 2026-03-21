// Highlight active nav link on scroll
const sections = document.querySelectorAll('.type-section');
const navLinks = document.querySelectorAll('.side-nav a:not(.nav-filter)');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(link => link.classList.remove('active'));
      const active = document.querySelector('.side-nav a[href="#' + entry.target.id + '"]');
      if (active) active.classList.add('active');
    }
  });
}, { rootMargin: '-10% 0px -80% 0px' });

sections.forEach(s => observer.observe(s));

// Inject qty badges on in-stock cards
document.querySelectorAll('.card').forEach(card => {
  if (card.classList.contains('shipped') || card.classList.contains('ordered') || card.classList.contains('backorder')) return;
  const model = card.querySelector('.model');
  if (!model) return;
  const qty = card.dataset.qty || '1';
  const badge = document.createElement('span');
  badge.className = 'qty-badge';
  badge.textContent = '\u00d7' + qty;
  model.appendChild(badge);
});

// Derive card properties from content
function getCardProps(card) {
  let status = 'in-stock';
  if (card.classList.contains('backorder')) status = 'backorder';
  else if (card.classList.contains('shipped')) status = 'shipped';
  else if (card.classList.contains('ordered')) status = 'ordered';

  const badge = card.querySelector('.brand-badge');
  let brand = 'wp';
  if (badge) {
    if (badge.src.includes('brand-ws')) brand = 'ws';
    else if (badge.src.includes('brand-cmt')) brand = 'cmt';
  }

  const shankCell = card.querySelector('.spec-common .spec-value');
  const shank = shankCell && shankCell.textContent.includes('1/2') ? '1/2' : '1/4';

  return { status, brand, shank };
}

// Unified filtering (multiselect per group)
function applyFilters() {
  const groups = {};
  document.querySelectorAll('.nav-filter.active').forEach(link => {
    const g = link.dataset.group;
    if (!groups[g]) groups[g] = new Set();
    groups[g].add(link.dataset.value);
  });

  document.querySelectorAll('.card-link').forEach(cardLink => {
    const card = cardLink.querySelector('.card');
    if (!card) return;
    const props = getCardProps(card);
    const visible = Object.keys(groups).every(g => groups[g].has(props[g]));
    cardLink.style.display = visible ? '' : 'none';
  });

  document.querySelectorAll('.type-section').forEach(section => {
    const visible = section.querySelectorAll('.card-link:not([style*="display: none"])');
    section.style.display = visible.length ? '' : 'none';
  });
}

document.querySelectorAll('.nav-filter').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    link.classList.toggle('active');
    applyFilters();
  });
});

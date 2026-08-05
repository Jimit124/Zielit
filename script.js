// Year
document.getElementById('year').textContent = new Date().getFullYear();

// Sticky nav shrink
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 40);
}, { passive: true });

// Mobile menu
const navToggle = document.getElementById('navToggle');
const mobileMenu = document.getElementById('mobileMenu');
navToggle.addEventListener('click', () => {
  navToggle.classList.toggle('open');
  mobileMenu.classList.toggle('open');
});
mobileMenu.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    navToggle.classList.remove('open');
    mobileMenu.classList.remove('open');
  });
});

// Scroll reveal — progressive enhancement only. Elements are visible by
// default (see CSS); only opt into the hidden/animate-in state if we can
// actually observe and reveal them, so a script failure or JS-disabled
// browser always shows full content.
const revealEls = document.querySelectorAll('.reveal');
const io = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in');
      io.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
revealEls.forEach(el => {
  el.classList.add('reveal-init');
  io.observe(el);
});

// Contact form -> real submission via FormSubmit.co, with mailto fallback
const form = document.getElementById('contactForm');
const submitBtn = document.getElementById('submitBtn');
const formNote = document.getElementById('formNote');
const formSuccess = document.getElementById('formSuccess');
const formError = document.getElementById('formError');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  formError.style.display = 'none';
  submitBtn.disabled = true;
  submitBtn.textContent = 'Sending…';

  const data = new FormData(form);

  try {
    const res = await fetch(form.action, {
      method: 'POST',
      body: data,
      headers: { 'Accept': 'application/json' }
    });

    if (!res.ok) throw new Error('Bad response');

    form.reset();
    formNote.style.display = 'none';
    formSuccess.style.display = 'block';
    submitBtn.textContent = 'Send message';
    submitBtn.disabled = false;

    setTimeout(() => {
      formSuccess.style.display = 'none';
      formNote.style.display = 'block';
    }, 7000);

  } catch (err) {
    // Network/service failed — fall back to opening the visitor's email client
    const name = data.get('name') || '';
    const email = data.get('email') || '';
    const company = data.get('company') || '';
    const channel = data.get('channel') || '';
    const message = data.get('message') || '';
    const subject = encodeURIComponent(`Marketing inquiry — ${channel}`);
    const body = encodeURIComponent(
      `Name: ${name}\nEmail: ${email}\nCompany: ${company}\nChannel: ${channel}\n\n${message}`
    );
    window.location.href = `mailto:info@zielit.com?subject=${subject}&body=${body}`;
    submitBtn.textContent = 'Send message';
    submitBtn.disabled = false;
    formError.style.display = 'block';
  }
});

// ==========================================================================
// MODERNIZATION PASS — layered on top of the existing behavior above.
// ==========================================================================

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const isTouch = window.matchMedia('(hover: none)').matches;

// Scroll progress bar
(function scrollProgress() {
  const bar = document.createElement('div');
  bar.className = 'scroll-progress';
  document.body.appendChild(bar);
  const update = () => {
    const h = document.documentElement;
    const scrolled = h.scrollTop;
    const max = h.scrollHeight - h.clientHeight;
    bar.style.width = max > 0 ? `${(scrolled / max) * 100}%` : '0%';
  };
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();

// Cursor spotlight over dark sections (hero + any .section-dark)
(function cursorSpotlight() {
  if (prefersReducedMotion || isTouch) return;
  const spot = document.createElement('div');
  spot.className = 'cursor-spotlight';
  document.body.appendChild(spot);
  const darkZones = document.querySelectorAll('.hero, .section-dark');
  let active = false;
  darkZones.forEach((zone) => {
    zone.addEventListener('mouseenter', () => { active = true; spot.classList.add('is-active'); });
    zone.addEventListener('mouseleave', () => { active = false; spot.classList.remove('is-active'); });
  });
  window.addEventListener('mousemove', (e) => {
    if (!active) return;
    spot.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
  }, { passive: true });
})();

// Subtle 3D tilt on capability / industry / perspective cards
(function tiltCards() {
  if (prefersReducedMotion || isTouch) return;
  const cards = document.querySelectorAll('.svc-card, .ind-card, .persp-card');
  cards.forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      const rotateX = (-y * 6).toFixed(2);
      const rotateY = (x * 8).toFixed(2);
      card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();

// Magnetic pull on primary CTA buttons
(function magneticButtons() {
  if (prefersReducedMotion || isTouch) return;
  const buttons = document.querySelectorAll('.btn-primary');
  buttons.forEach((btn) => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      btn.style.transform = `translate(${(x * 0.18).toFixed(1)}px, ${(y * 0.35).toFixed(1)}px)`;
    });
    btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
  });
})();

// Count-up animation for the "who we are" stat trio (3 / 1 / 0)
(function countUpStats() {
  const stats = document.querySelectorAll('.about-stats strong');
  if (!stats.length) return;
  const animate = (el) => {
    const target = parseInt(el.textContent, 10);
    if (Number.isNaN(target) || prefersReducedMotion) return;
    const duration = 900;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = target;
    };
    requestAnimationFrame(tick);
  };
  const statIo = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animate(entry.target);
        statIo.unobserve(entry.target);
      }
    });
  }, { threshold: 0.6 });
  stats.forEach((el) => statIo.observe(el));
})();

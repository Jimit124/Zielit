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

// Scroll reveal
const revealEls = document.querySelectorAll('.reveal');
const io = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in');
      io.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
revealEls.forEach(el => io.observe(el));

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

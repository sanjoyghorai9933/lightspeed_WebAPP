/* ═══════════════════════════════════════════════════════
   LIGHTSEED — Main JavaScript
   Scroll animations, form handling, counters, tilt, etc.
   ═══════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ── SCROLL PROGRESS BAR ──────────────────────────────
  const progressBar = document.getElementById('scrollProgress');
  function updateProgress() {
    if (!progressBar) return;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    progressBar.style.setProperty('--progress', total > 0 ? window.scrollY / total : 0);
  }

  // ── NAVBAR SCROLL ────────────────────────────────────
  const navbar = document.querySelector('.ls-navbar');
  function updateNavbar() {
    if (!navbar) return;
    // Toggle between transparent and solid navbar
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  }

  // Initialize based on current scroll position
  updateNavbar();

  // ── RAF-BATCHED SCROLL ───────────────────────────────
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        updateProgress();
        updateNavbar();
        updateParallax();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  updateNavbar();
  updateProgress();

  // ── INTERSECTION OBSERVER — scroll animations ─────────
  const animObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        el.classList.add('is-visible');
        if (el.dataset.count !== undefined) startCounter(el);
        animObserver.unobserve(el);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

  document.querySelectorAll('[data-anim]').forEach(el => animObserver.observe(el));

  // Auto-stagger children --------------------------------
  document.querySelectorAll('[data-stagger]').forEach(parent => {
    const base = parseInt(parent.dataset.stagger) || 100;
    Array.from(parent.children).forEach((child, i) => {
      if (!child.dataset.anim) child.setAttribute('data-anim', 'fade-up');
      child.setAttribute('data-delay', String(i * base));
      animObserver.observe(child);
    });
  });

  // ── COUNTER ANIMATION ────────────────────────────────
  function startCounter(el) {
    const target   = parseFloat(el.dataset.count);
    const suffix   = el.dataset.suffix || '';
    const prefix   = el.dataset.prefix || '';
    const duration = 1800;
    const start    = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 4);
      const val  = target < 10 ? (ease * target).toFixed(1) : Math.round(ease * target);
      el.textContent = prefix + val.toLocaleString() + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  // ── PARALLAX ─────────────────────────────────────────
  function updateParallax() {
    document.querySelectorAll('[data-parallax]').forEach(el => {
      const rect   = el.getBoundingClientRect();
      const center = rect.top + rect.height / 2 - window.innerHeight / 2;
      const speed  = parseFloat(el.dataset.parallax) || 0.15;
      el.style.transform = `translateY(${center * speed}px)`;
    });
  }

  // ── CARD TILT ─────────────────────────────────────────
  document.querySelectorAll('.ls-hero-card, .ls-pillar').forEach(card => {
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width  - 0.5;
      const y = (e.clientY - r.top)  / r.height - 0.5;
      card.style.transform = `perspective(700px) rotateY(${x * 9}deg) rotateX(${-y * 7}deg) translateY(-4px)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transition = 'transform 0.55s cubic-bezier(0.22,1,0.36,1)';
      card.style.transform  = '';
      setTimeout(() => { card.style.transition = ''; }, 600);
    });
  });

  // ── PARTICLES ────────────────────────────────────────
  document.querySelectorAll('.ls-particles').forEach(container => {
    for (let i = 0; i < 20; i++) {
      const p = document.createElement('div');
      p.className = 'ls-particle';
      const size = Math.random() * 5 + 2;
      Object.assign(p.style, {
        width:  size + 'px',
        height: size + 'px',
        left:   (Math.random() * 100) + '%',
        bottom: '0',
        animationDuration:  (Math.random() * 12 + 8) + 's',
        animationDelay:     (Math.random() * 10) + 's',
      });
      container.appendChild(p);
    }
  });

  // ── ENQUIRY FORM ──────────────────────────────────────
  const enquiryForm = document.getElementById('enquiryForm');
  if (enquiryForm) {
    enquiryForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const btn   = this.querySelector('[type=submit]');
      const alert = document.getElementById('formAlert');
      const data  = Object.fromEntries(new FormData(this));
      btn.disabled = true;
      btn.textContent = 'Sending…';
      try {
        const res = await fetch('/api/enquiry', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const json = await res.json();
        showAlert(alert, json.message || 'Sent!', json.success ? 'success' : 'error');
        if (json.success) this.reset();
      } catch (err) {
        showAlert(alert, 'Something went wrong. Please try again.', 'error');
      }
      btn.disabled    = false;
      btn.textContent = 'Send Message';
    });
  }

  // ── NEWSLETTER FORM ───────────────────────────────────
  const newsForm = document.getElementById('newsletterForm');
  if (newsForm) {
    newsForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const btn   = this.querySelector('[type=submit]');
      const alert = document.getElementById('newsletterAlert');
      const data  = Object.fromEntries(new FormData(this));
      btn.disabled = true;
      try {
        const res  = await fetch('/api/newsletter', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const json = await res.json();
        showAlert(alert, json.message, json.success ? 'success' : 'error');
        if (json.success) this.reset();
      } catch {
        showAlert(alert, 'Something went wrong.', 'error');
      }
      btn.disabled = false;
    });
  }

  function showAlert(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className   = 'ls-alert ' + type + ' show';
    setTimeout(() => { el.classList.remove('show'); }, 5000);
  }

  // ── FEED TABS ─────────────────────────────────────────
  window.switchFeed = function(type) {
    const grid = document.getElementById('feedGrid');
    if (!grid) return;
    const feeds = {
      instagram: [
        { emoji:'📸', text:'Behind the scenes — Praankosh breathwork session.', bg:'linear-gradient(135deg,#F5E0FF,#E8C8FF)' },
        { emoji:'🌿', text:'Leadership is presence before performance.', bg:'linear-gradient(135deg,#D4E8DE,#D0EEEB)' },
        { emoji:'✨', text:'New Shuddhi cohort begins. Safety starts within.', bg:'linear-gradient(135deg,#FBF4CC,#FDE8A0)' },
        { emoji:'🕊️', text:'Saarthi — a space for clarity and courage.', bg:'linear-gradient(135deg,#EDE8F5,#E0D8F0)' },
        { emoji:'🎓', text:'FDP Day 2 — educators becoming facilitators.', bg:'linear-gradient(135deg,#D4E8DE,#FAF6EE)' },
        { emoji:'💛', text:'Reflection circles — healing together.', bg:'linear-gradient(135deg,#FFF0D8,#FFE8CC)' },
      ],
      youtube: [
        { emoji:'▶', text:'What is emotional intelligence in leadership?', bg:'linear-gradient(135deg,#FFE8E8,#FFD0D0)' },
        { emoji:'▶', text:'Praankosh — introduction to breathwork.', bg:'linear-gradient(135deg,#D4E8DE,#D0EEEB)' },
        { emoji:'▶', text:'POSH awareness — what every employee must know.', bg:'linear-gradient(135deg,#FBF4CC,#FDE8A0)' },
        { emoji:'▶', text:'From campus to corporate — the readiness gap.', bg:'linear-gradient(135deg,#D6E8F7,#D0E4FF)' },
      ],
      linkedin: [
        { emoji:'in', text:'Why awareness precedes policy in safe institutions.', bg:'linear-gradient(135deg,#D6E8F7,#C8DCF5)' },
        { emoji:'in', text:'The real ROI of emotional intelligence in leadership.', bg:'linear-gradient(135deg,#FAF6EE,#F0E9D8)' },
        { emoji:'in', text:'Lightseed Shuddhi — building safety cultures.', bg:'linear-gradient(135deg,#FFE8CC,#FFF0D8)' },
        { emoji:'in', text:'Faculty who lead — not just teach.', bg:'linear-gradient(135deg,#D4E8DE,#D0EEEB)' },
      ],
    };
    const items = feeds[type] || feeds.instagram;
    grid.style.opacity   = '0';
    grid.style.transform = 'translateY(10px)';
    setTimeout(() => {
      grid.innerHTML = items.map(f => `
        <div class="col-6 col-sm-4 col-lg-2">
          <div class="ls-feed-card" style="background:${f.bg};">
            <div class="ls-feed-inner">
              <div style="font-size:1.8rem;">${f.emoji}</div>
              <p>${f.text}</p>
            </div>
          </div>
        </div>`).join('');
      grid.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
      grid.style.opacity    = '1';
      grid.style.transform  = 'translateY(0)';
    }, 180);
  };

  // ── BACK TO TOP ───────────────────────────────────────
  const topBtn = document.getElementById('backToTop');
  if (topBtn) {
    window.addEventListener('scroll', () => {
      topBtn.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });
    topBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  // ── ACTIVE NAV ───────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.ls-navbar .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) link.classList.add('active');
    if (href === '/' && currentPath === '/') link.classList.add('active');
  });

});

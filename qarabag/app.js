/* ============================================================
   Karabakh BSc Economics — Deck navigation & course modal
   ============================================================ */

(function () {
  'use strict';

  const deck = document.getElementById('deck');
  const slides = Array.from(deck.querySelectorAll('.slide'));
  const dotsRoot = document.getElementById('navDots');
  const counter = document.getElementById('navCounter');
  const indicator = document.getElementById('slideIndicator');
  const arrowL = document.getElementById('navPrev');
  const arrowR = document.getElementById('navNext');

  // ── Build dots ─────────────────────────────────────────────
  slides.forEach((slide, i) => {
    const dot = document.createElement('button');
    dot.className = 'nav-dot';
    dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
    dot.addEventListener('click', () => goTo(i));
    dotsRoot.appendChild(dot);
  });
  const dots = Array.from(dotsRoot.querySelectorAll('.nav-dot'));

  // ── Active-slide tracking ──────────────────────────────────
  let current = 0;
  function setActive(i) {
    current = i;
    dots.forEach((d, k) => d.classList.toggle('is-active', k === i));
    counter.textContent = String(i + 1).padStart(2, '0') + ' / ' + String(slides.length).padStart(2, '0');

    const s = slides[i];
    const label = s.dataset.title || '';
    const section = s.dataset.section || '';
    indicator.innerHTML = `<span class="idx">${String(i + 1).padStart(2, '0')} — ${label}</span><span class="section">${section}</span>`;

    // Body class for tone-aware chrome
    document.body.dataset.tone = s.dataset.tone || 'light';

    // Notify host (for speaker-notes integration if ever needed)
    try { window.parent.postMessage({ slideIndexChanged: i }, '*'); } catch (e) {}
  }

  function goTo(i) {
    i = Math.max(0, Math.min(slides.length - 1, i));
    deck.scrollTo({ left: i * window.innerWidth, behavior: 'smooth' });
    // setActive will fire from scroll handler
  }

  // ── Scroll → which slide is most visible
  let scrollRaf = null;
  deck.addEventListener('scroll', () => {
    if (scrollRaf) cancelAnimationFrame(scrollRaf);
    scrollRaf = requestAnimationFrame(() => {
      const idx = Math.round(deck.scrollLeft / window.innerWidth);
      if (idx !== current) setActive(idx);
    });
  });

  arrowL.addEventListener('click', () => goTo(current - 1));
  arrowR.addEventListener('click', () => goTo(current + 1));

  // ── Keyboard ───────────────────────────────────────────────
  window.addEventListener('keydown', (e) => {
    if (modal.classList.contains('is-open')) {
      if (e.key === 'Escape') closeModal();
      return;
    }
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
      e.preventDefault();
      goTo(current + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      goTo(current - 1);
    } else if (e.key === 'Home') {
      e.preventDefault();
      goTo(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      goTo(slides.length - 1);
    }
  });

  // ── Resize: keep current slide centered ────────────────────
  window.addEventListener('resize', () => {
    deck.scrollTo({ left: current * window.innerWidth, behavior: 'auto' });
  });

  // ── Initial state ──────────────────────────────────────────
  setActive(0);

  /* ============================================================
     COURSE MODAL
     ============================================================ */

  const modal = document.getElementById('courseModal');
  const backdrop = document.getElementById('modalBackdrop');
  const panel = modal.querySelector('.modal-panel');

  function openCourse(id) {
    const data = window.COURSES[id];
    if (!data) {
      console.warn('Unknown course id:', id);
      return;
    }
    panel.innerHTML = buildCourseMarkup(id, data);
    panel.scrollTop = 0;
    modal.classList.add('is-open');
    backdrop.classList.add('is-open');
    modal.style.pointerEvents = 'auto';

    panel.querySelector('.modal-close').addEventListener('click', closeModal);
  }

  function closeModal() {
    modal.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    setTimeout(() => { modal.style.pointerEvents = 'none'; }, 400);
  }

  backdrop.addEventListener('click', closeModal);

  function buildCourseMarkup(id, c) {
    const outcomes = (c.outcomes || []).map(o => `<li>${o}</li>`).join('');
    const topics = (c.topics || []).map(t => `<span class="topic">${t}</span>`).join('');

    return `
      <button class="modal-close" aria-label="Close">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M1 1 L13 13 M13 1 L1 13"/></svg>
      </button>

      <div class="modal-eyebrow">
        <span>${c.code || ''}</span>
        <span class="pill">${c.type || 'Module'}</span>
        <span>${c.semester || ''}</span>
      </div>

      <h2 class="modal-title">${c.title}</h2>
      <p class="modal-summary">${c.summary || ''}</p>

      <div class="modal-grid">
        <div class="cell">
          <div class="label">Credits</div>
          <div class="value">${c.credits || '—'} ECTS</div>
        </div>
        <div class="cell">
          <div class="label">Delivery</div>
          <div class="value">Lectures + Seminars + Labs</div>
        </div>
      </div>

      <section class="modal-section">
        <h4>Learning Outcomes</h4>
        <ul>${outcomes}</ul>
      </section>

      <section class="modal-section">
        <h4>Indicative Topics</h4>
        <div class="modal-topics">${topics}</div>
      </section>

      <section class="modal-section">
        <h4>Assessment</h4>
        <p style="font-family: var(--font-display); font-size: 22px; line-height: 1.3; color: var(--green-ink);">${c.assessment || 'To be confirmed.'}</p>
      </section>

      <div style="margin-top:auto; padding-top: 28px; border-top: 1px solid rgba(20,32,30,0.12);">
        <div style="display:flex; justify-content:space-between; align-items:center; font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.18em; text-transform:uppercase; color: var(--ink-mute);">
          <span>Qarabağ Universiteti · BSc Economics</span>
          <span>${c.code || ''}</span>
        </div>
      </div>
    `;
  }

  // ── Global click delegate for .course cards ────────────────
  document.addEventListener('click', (e) => {
    const card = e.target.closest('[data-course]');
    if (!card) return;
    openCourse(card.dataset.course);
  });

})();

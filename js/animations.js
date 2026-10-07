/* ============================================================
   CRJ Fastigheter AB — Animations
   ============================================================ */

'use strict';

/* ---- Lock scroll immediately if intro should play ---- */
const _introEl = document.getElementById('site-intro');
if (_introEl && !sessionStorage.getItem('crj_intro_played')) {
  document.body.style.overflow = 'hidden';
}

/* ---- Scroll Progress Bar ---- */
(function initScrollProgress() {
  const bar = document.createElement('div');
  bar.id = 'scroll-progress';
  document.body.prepend(bar);

  const update = () => {
    const scrolled = window.scrollY;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = total > 0 ? (scrolled / total * 100) + '%' : '0%';
  };
  window.addEventListener('scroll', update, { passive: true });
})();

/* ---- Building Window Glow ---- */
(function initBuildingGlow() {
  document.querySelectorAll('.building-svg').forEach(svg => {
    const whites = svg.querySelectorAll('rect');
    whites.forEach((rect, i) => {
      const fill = rect.getAttribute('fill') || '';
      if (fill.includes('rgba(255,255,255')) {
        rect.classList.add('win-pulse');
        rect.style.animationDelay = (i * 0.45) + 's';
      } else if (fill.includes('rgba(200,169,110')) {
        rect.classList.add('win-pulse-g');
        rect.style.animationDelay = (i * 0.6 + 0.4) + 's';
      }
    });
  });
})();

/* ---- Section Tag Visibility ---- */
(function initSectionTags() {
  const tags = document.querySelectorAll('.section-tag');
  if (!tags.length) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.2 });
  tags.forEach(t => obs.observe(t));
})();

/* ---- Animated Dividers ---- */
(function initDividers() {
  document.querySelectorAll('.divider').forEach(d => {
    d.classList.add('divider--animated');
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });
    obs.observe(d);
  });
})();

/* ---- Intro Animation (homepage only) ---- */
(function initIntro() {
  const overlay = document.getElementById('site-intro');
  if (!overlay) return;

  if (sessionStorage.getItem('crj_intro_played')) {
    overlay.remove();
    document.body.style.overflow = '';
    return;
  }

  if (typeof gsap === 'undefined') {
    sessionStorage.setItem('crj_intro_played', '1');
    overlay.remove();
    document.body.style.overflow = '';
    return;
  }

  const mark       = overlay.querySelector('.intro__mark');
  const nameInner  = overlay.querySelector('.intro__name-inner');
  const line       = overlay.querySelector('.intro__line');
  const sub        = overlay.querySelector('.intro__sub');
  const curtainTop = overlay.querySelector('.intro__curtain--top');
  const curtainBot = overlay.querySelector('.intro__curtain--bottom');

  // Safeguard: always unlock after 5s max
  const safetyTimer = setTimeout(() => {
    sessionStorage.setItem('crj_intro_played', '1');
    overlay.remove();
    document.body.style.overflow = '';
  }, 5000);

  const tl = gsap.timeline({
    onComplete() {
      clearTimeout(safetyTimer);
      sessionStorage.setItem('crj_intro_played', '1');
      document.body.style.overflow = '';
      overlay.style.pointerEvents = 'none';
      setTimeout(() => {
        overlay.remove();
        initHeroEntrance(true);
      }, 80);
    }
  });

  tl
    .to(mark, {
      opacity: 1, scale: 1, y: 0,
      duration: 0.65, ease: 'back.out(1.7)',
      delay: 0.2
    })
    .to(nameInner, {
      y: '0%',
      duration: 0.55, ease: 'power3.out'
    }, '-=0.3')
    .to(line, {
      width: 72,
      duration: 0.45, ease: 'power2.out'
    }, '-=0.25')
    .to(sub, {
      opacity: 1,
      duration: 0.35, ease: 'power2.out'
    }, '-=0.2')
    // Pause to let it breathe
    .to({}, { duration: 0.75 })
    // Content exits upward
    .to([mark, nameInner, sub], {
      opacity: 0, y: -20,
      duration: 0.32, ease: 'power2.in',
      stagger: 0.05
    })
    .to(line, { opacity: 0, duration: 0.25 }, '<')
    // Curtains split — top up, bottom down
    .to(curtainTop, {
      yPercent: -100,
      duration: 0.88, ease: 'power3.inOut'
    }, '-=0.05')
    .to(curtainBot, {
      yPercent: 100,
      duration: 0.88, ease: 'power3.inOut'
    }, '<');

  // Set hero invisible now, animate in after intro
  const heroEls = [
    document.querySelector('.hero__tag'),
    document.querySelector('.hero__title'),
    document.querySelector('.hero__subtitle'),
    document.querySelector('.hero__actions'),
    document.querySelector('.hero__scroll'),
  ].filter(Boolean);
  if (heroEls.length) {
    gsap.set(heroEls, { opacity: 0, y: 28 });
  }
})();

/* ---- Hero Entrance (called after intro or directly on non-intro visits) ---- */
function initHeroEntrance(afterIntro) {
  if (typeof gsap === 'undefined') return;
  const heroEls = [
    document.querySelector('.hero__tag'),
    document.querySelector('.hero__title'),
    document.querySelector('.hero__subtitle'),
    document.querySelector('.hero__actions'),
    document.querySelector('.hero__scroll'),
  ].filter(Boolean);

  if (!heroEls.length) return;

  const delay = afterIntro ? 0.1 : 0.25;
  gsap.to(heroEls, {
    opacity: 1, y: 0,
    duration: 0.65,
    ease: 'power3.out',
    stagger: 0.1,
    delay
  });
}

/* ---- On non-intro load: still animate hero ---- */
(function () {
  if (document.getElementById('site-intro')) return; // intro handles it
  initHeroEntrance(false);
})();

/* ---- Stats Bar Stagger ---- */
(function initStatsStagger() {
  const items = document.querySelectorAll('.stats-bar__item');
  if (!items.length || typeof gsap === 'undefined') return;

  gsap.set(items, { opacity: 0, y: 20 });
  const obs = new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) {
      gsap.to(items, {
        opacity: 1, y: 0,
        duration: 0.55,
        ease: 'power2.out',
        stagger: 0.09
      });
      obs.disconnect();
    }
  }, { threshold: 0.3 });
  items.forEach(i => obs.observe(i));
})();

/* ---- Queue Page: animated position counter ---- */
(function initQueueCounter() {
  const el = document.querySelector('[data-queue-pos]');
  if (!el || typeof gsap === 'undefined') return;
  const target = parseInt(el.dataset.queuePos, 10);
  if (isNaN(target)) return;

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        gsap.from(el, {
          textContent: 0,
          duration: 1.2,
          ease: 'power2.out',
          snap: { textContent: 1 },
          onUpdate() {
            el.textContent = Math.ceil(parseFloat(el.textContent));
          }
        });
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.6 });
  obs.observe(el);
})();

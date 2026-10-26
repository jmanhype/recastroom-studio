/* SPDX-License-Identifier: MIT */
(() => {
  'use strict';

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const tagline = document.querySelector('[data-tagline]');
  if (tagline && !reduceMotion) {
    const words = tagline.textContent.trim().split(/\s+/);
    tagline.replaceChildren(...words.flatMap((word, index) => {
      const item = document.createElement('span');
      item.textContent = word;
      item.style.transitionDelay = `${index * 120}ms`;
      return [item, document.createTextNode(' ')];
    }));
  }

  const sections = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('in');
      revealObserver.unobserve(entry.target);
    }
  }, { threshold: .25 });
  sections.forEach((section) => revealObserver.observe(section));

  if (tagline) {
    const wordObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        tagline.querySelectorAll('span').forEach((word) => word.classList.add('active'));
        wordObserver.unobserve(tagline);
      }
    }, { threshold: .5 });
    wordObserver.observe(tagline);
  }

  const cards = Array.from(document.querySelectorAll('.feature-card'));
  const running = new Set();
  const cardIndexes = new Map(cards.map((card, index) => [card, index]));
  let frameRequest = null;
  const cardObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const card = entry.target;
      if (entry.isIntersecting) {
        card.classList.add('in');
        if (!reduceMotion) {
          running.add(card);
          if (frameRequest === null) frameRequest = requestAnimationFrame(renderFrame);
        }
      } else {
        running.delete(card);
        if (running.size === 0 && frameRequest !== null) {
          cancelAnimationFrame(frameRequest);
          frameRequest = null;
        }
      }
    }
  }, { threshold: .3 });
  cards.forEach((card) => cardObserver.observe(card));

  if (reduceMotion) return;

  const wave = (value) => .5 + .5 * Math.sin(value);
  function renderFrame(now) {
    if (running.size === 0) {
      frameRequest = null;
      return;
    }
    const time = now / 1000;
    running.forEach((card) => story(card, time));
    frameRequest = requestAnimationFrame(renderFrame);
  }
  function story(card, time) {
    const kind = card.dataset.story;
    const t = time + (cardIndexes.get(card) || 0) * .55;
    card.style.setProperty('--story-t', String(t));
    if (kind === 'source') {
      const scan = card.querySelector('.source-scan');
      if (scan) scan.style.transform = `translateY(-50%) scaleX(${.2 + .8 * wave(t * .7)})`;
    }
    if (kind === 'reference') {
      const chip = card.querySelector('.reference-chip');
      if (chip) {
        const value = wave(t * .55);
        chip.style.opacity = String(.3 + .7 * value);
        chip.style.transform = `translate(-50%,-50%) scale(${.86 + .1 * value})`;
      }
    }
    if (kind === 'rights') {
      card.querySelectorAll('.rights-stage span').forEach((badge, index) => {
        const local = Math.max(0, Math.min(1, (t - index * .55) % 2.2 / 1));
        badge.style.opacity = String(.45 + .55 * local);
      });
    }
    if (kind === 'render') {
      const pulse = card.querySelector('.render-pulse');
      if (pulse) pulse.style.transform = `translate(${((t * 38) % 240) - 24}px,-50%)`;
    }
    if (kind === 'audio') {
      card.querySelectorAll('.wave i').forEach((bar, index) => {
        const value = wave(t * 2 + index * .7);
        bar.style.opacity = String(.45 + .45 * value);
      });
    }
    if (kind === 'review') {
      const scan = card.querySelector('.review-scan');
      if (scan) scan.style.transform = `translateY(calc(-50% + ${(wave(t * .6) * 64 - 32)}px))`;
    }
  }

})();

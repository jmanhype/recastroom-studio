/* SPDX-License-Identifier: MIT */
/* RecastRoom first-run wizard and workspace tour: welcome → connection → tour → done.
   Skippable, reopenable from the Help button or the studio:open-help event.
   Plain pages, no framework: an IIFE that talks to /api/settings and /api/health. */
(() => {
  "use strict";

  const SETUP_KEY = "recastroom.setupDone";
  const PROVIDERS = [
    { id: "dry_run", label: "Dry run", blurb: "Local rehearsal. No AI generation and no renderer needed." },
    { id: "legacy", label: "Local ComfyUI", blurb: "Your ComfyUI HTTP address runs the MiniMax H3 graph." },
    { id: "sdk", label: "Comfy API · SDK", blurb: "The official Comfy SDK with an API key." },
  ];
  const STEPS = ["welcome", "connection", "tour", "done"];
  const TOUR_STOPS = [
    {
      target: ".steps",
      title: "Four steps, one desk",
      body: "Select media, prepare the workflow, run it, review the result. The number that lights up is where you are.",
    },
    {
      target: "#readiness",
      title: "Live readiness",
      body: "Six cells watch your dependencies: source, reference, attestation, workflow, renderer, execution. Everything green means you can prepare.",
    },
    {
      target: "#workflow-catalog",
      title: "Workflow studio",
      body: "The Recast Room is the production flagship. Concept lanes stay visible without pretending to be ready.",
    },
    {
      target: "#source",
      title: "The original",
      body: "Your clip carries the performance and the dialogue. Nothing is uploaded until you prepare, and Archive.org discovery is one panel below.",
    },
    {
      target: "#reference_1",
      title: "The new cast",
      body: "One required reference drives the replacement likeness; a second adds perspective. Saved characters reuse references across jobs.",
    },
    {
      target: "#advanced",
      title: "Timing & creative controls",
      body: "Optional Whisper word timings lock dialogue to frames, plus identity description, seed, and a custom C1-compatible workflow.",
    },
    {
      target: "#rights",
      title: "The production checkpoint",
      body: "RecastRoom requires a recorded operator attestation before generation. It is a declaration by you, not legal clearance.",
    },
    {
      target: "#submit",
      title: "Prepare, then run",
      body: "Prepare validates and builds the workflow. Run sends it to the renderer you configured in this wizard. Review compares source and final side by side.",
    },
  ];

  const $ = (id) => document.getElementById(id);
  const storage = {
    get(key) { try { return window.localStorage.getItem(key); } catch (_) { return null; } },
    set(key, value) { try { window.localStorage.setItem(key, value); } catch (_) { /* private mode */ } },
  };
  const reducedMotion = () => Boolean(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  let stepIndex = 0;
  let selectedBackend = "dry_run";
  let settingsLoaded = false;
  let touring = false;
  let tourIndex = 0;
  let tourSpot = null;

  function isActive() { return !$("wizard").hidden || touring; }

  function open(at) {
    $("wizard").hidden = false;
    stepIndex = Math.max(0, STEPS.indexOf(at || "welcome"));
    if (stepIndex === STEPS.length - 1 && at === undefined) stepIndex = 0;
    render();
    if (STEPS[stepIndex] === "connection") loadSettings();
  }

  function close() {
    endTour();
    $("wizard").hidden = true;
  }

  function finish() {
    storage.set(SETUP_KEY, "1");
    close();
  }

  function render() {
    const step = STEPS[stepIndex];
    for (const name of STEPS) {
      const pane = $("wizard-" + name);
      if (pane) pane.hidden = name !== step;
    }
    document.querySelectorAll("#wizard-progress li").forEach((dash, index) => {
      dash.classList.toggle("current", index === stepIndex);
      dash.classList.toggle("done", index < stepIndex);
    });
    $("wizard-title").textContent =
      step === "welcome" ? "Welcome to RecastRoom" :
      step === "connection" ? "Where videos are generated" :
      step === "tour" ? "A quick look around" : "All set";
    $("wizard-back").hidden = stepIndex === 0;
    $("wizard-skip").textContent = stepIndex === STEPS.length - 1 ? "" : (stepIndex === 0 ? "Skip setup" : "Skip");
    $("wizard-skip").hidden = stepIndex === STEPS.length - 1;
    $("wizard-next").textContent =
      step === "welcome" ? "Start" :
      step === "tour" ? "Start the tour" :
      step === "done" ? "Open the studio" : "Next";
    if (step === "connection") loadSettings();
  }

  function next() {
    const step = STEPS[stepIndex];
    if (step === "tour") { startTour(); return; }
    if (stepIndex >= STEPS.length - 1) { finish(); return; }
    stepIndex += 1;
    render();
  }

  function back() {
    if (touring) { stepTour(-1); return; }
    if (stepIndex > 0) { stepIndex -= 1; render(); }
  }

  /* ---- Connection step ---- */

  async function loadSettings() {
    if (settingsLoaded) return;
    let payload = null;
    try {
      const response = await fetch("/api/settings");
      if (response.ok) payload = await response.json();
    } catch (_) { payload = null; }
    if (!payload) {
      $("wizard-connection-note").textContent = "The saved connection could not be read. You can still test an address.";
      return;
    }
    settingsLoaded = true;
    selectedBackend = payload.backend || "dry_run";
    renderProviders(payload);
    const url = $("wizard-url");
    url.value = payload.fields.comfy_url && payload.fields.comfy_url.source !== "default" ? payload.comfy_url : "";
    url.disabled = payload.fields.comfy_url.locked;
    url.placeholder = payload.comfy_url || "http://127.0.0.1:8188";
    const key = $("wizard-key");
    key.value = "";
    key.disabled = payload.fields.comfy_api_key.locked;
    key.placeholder = payload.has_api_key && payload.api_key_hint
      ? "saved " + payload.api_key_hint + " · leave blank to keep"
      : "comfyui-…";
    const locks = payload.locked || [];
    $("wizard-lock-note").hidden = locks.length === 0;
    if (locks.length) {
      $("wizard-lock-note").textContent = "Locked by the launch environment: " + locks.join(", ") + ". Change them in RECASTROOM_* variables and restart.";
    }
  }

  function renderProviders(payload) {
    const group = $("wizard-providers");
    group.textContent = "";
    for (const provider of PROVIDERS) {
      const locked = payload && payload.fields && payload.fields.backend && payload.fields.backend.locked;
      const active = selectedBackend === provider.id;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "provider-card" + (active ? " active" : "");
      button.dataset.backend = provider.id;
      button.setAttribute("aria-pressed", active ? "true" : "false");
      if (locked) button.disabled = provider.id !== selectedBackend;
      const title = document.createElement("strong");
      title.textContent = provider.label;
      const blurb = document.createElement("span");
      blurb.textContent = provider.blurb;
      button.append(title, blurb);
      if (active && payload && payload.backend === provider.id) {
        const chip = document.createElement("em");
        chip.className = "in-use";
        chip.textContent = "in use";
        button.append(chip);
      }
      button.addEventListener("click", () => {
        selectedBackend = provider.id;
        renderProviders(payload);
        setCallout(null);
      });
      group.append(button);
    }
  }

  function draft() {
    const payload = { backend: selectedBackend };
    const url = $("wizard-url").value.trim();
    const key = $("wizard-key").value;
    if (url) payload.comfy_url = url;
    if (key) payload.comfy_api_key = key;
    return payload;
  }

  function setCallout(verdict) {
    const callout = $("wizard-test-result");
    if (!verdict) { callout.hidden = true; callout.textContent = ""; callout.className = "wizard-callout"; return; }
    callout.hidden = false;
    callout.className = "wizard-callout " + (verdict.ok ? "ok" : "error");
    callout.textContent = (verdict.ok ? "✓ " : "✗ ") + verdict.message;
    callout.setAttribute("aria-live", "polite");
  }

  async function postSettings(path, body) {
    const response = await fetch("/api/settings" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let payload = null;
    try { payload = await response.json(); } catch (_) { payload = null; }
    return { status: response.status, payload };
  }

  async function testConnection() {
    const button = $("wizard-test");
    button.disabled = true;
    button.textContent = "Testing…";
    setCallout(null);
    try {
      const outcome = await postSettings("/test", draft());
      if (outcome.status === 200 && outcome.payload) {
        setCallout(outcome.payload);
      } else {
        const detail = outcome.payload && outcome.payload.detail;
        setCallout({ ok: false, message: (detail && detail.message) || (typeof detail === "string" ? detail : "The connection could not be tested.") });
      }
    } catch (_) {
      setCallout({ ok: false, message: "The studio server did not answer. Check that it is still running." });
    } finally {
      button.disabled = false;
      button.textContent = "Test connection";
    }
  }

  async function saveConnection() {
    const button = $("wizard-save");
    button.disabled = true;
    button.textContent = "Saving…";
    setCallout(null);
    try {
      const outcome = await postSettings("", draft());
      if (outcome.status === 200 && outcome.payload) {
        settingsLoaded = false;
        await loadSettings();
        setCallout({ ok: true, message: outcome.payload.message + " · saved and in use" });
        const retry = document.getElementById("health-retry");
        if (retry) retry.click();
        document.dispatchEvent(new CustomEvent("wizard:connection-saved", { detail: outcome.payload }));
      } else {
        const detail = outcome.payload && outcome.payload.detail;
        setCallout({ ok: false, message: (detail && (detail.message || detail)) || "The connection could not be saved." });
      }
    } catch (_) {
      setCallout({ ok: false, message: "The studio server did not answer. Check that it is still running." });
    } finally {
      button.disabled = false;
      button.textContent = "Save and use";
    }
  }

  /* ---- Tour ---- */

  function spotFor(stop) { return document.querySelector(stop.target); }

  function startTour() {
    $("wizard").hidden = true;
    touring = true;
    tourIndex = 0;
    showStop();
  }

  function stepTour(direction) {
    tourIndex += direction;
    if (tourIndex < 0) { endTour(); $("wizard").hidden = false; stepIndex = STEPS.indexOf("tour"); render(); return; }
    if (tourIndex >= TOUR_STOPS.length) { finish(); return; }
    showStop();
  }

  function showStop() {
    clearSpot();
    const stop = TOUR_STOPS[tourIndex];
    const spot = spotFor(stop);
    if (!spot) { stepTour(1); return; }
    tourSpot = spot;
    spot.classList.add("tour-spot");
    spot.scrollIntoView({ block: "center", behavior: reducedMotion() ? "auto" : "smooth" });
    const card = $("tour-card");
    $("tour-count").textContent = (tourIndex + 1) + " / " + TOUR_STOPS.length;
    $("tour-title").textContent = stop.title;
    $("tour-body").textContent = stop.body;
    $("tour-back").hidden = tourIndex === 0;
    $("tour-next").textContent = tourIndex === TOUR_STOPS.length - 1 ? "Done" : "Next";
    card.hidden = false;
    positionCard(card, spot);
  }

  function positionCard(card, spot) {
    const rect = spot.getBoundingClientRect();
    card.style.left = "0px";
    card.style.top = "0px";
    const box = card.getBoundingClientRect();
    const margin = 12;
    let left = Math.min(
      Math.max(margin, rect.left + rect.width / 2 - box.width / 2),
      window.innerWidth - box.width - margin
    );
    let top = rect.bottom + margin;
    if (top + box.height > window.innerHeight - margin) top = rect.top - box.height - margin;
    if (top < margin) top = margin;
    card.style.left = left + "px";
    card.style.top = top + "px";
  }

  function clearSpot() {
    if (tourSpot) tourSpot.classList.remove("tour-spot");
    tourSpot = null;
  }

  function endTour() {
    if (!touring) return;
    touring = false;
    clearSpot();
    $("tour-card").hidden = true;
  }

  /* ---- Wiring ---- */

  function automatedSession() {
    // Playwright and friends set navigator.webdriver; their evidence journeys
    // expect the plain desk, so the first-run wizard stays out of their way.
    try { return Boolean(window.navigator && window.navigator.webdriver); } catch (_) { return false; }
  }

  function wire() {
    $("wizard-next").addEventListener("click", next);
    $("wizard-back").addEventListener("click", back);
    $("wizard-skip").addEventListener("click", finish);
    $("wizard-test").addEventListener("click", testConnection);
    $("wizard-save").addEventListener("click", saveConnection);
    $("wizard-start-tour").addEventListener("click", startTour);
    $("wizard-done-tour").addEventListener("click", finish);
    $("tour-next").addEventListener("click", () => stepTour(1));
    $("tour-back").addEventListener("click", () => stepTour(-1));
    $("tour-exit").addEventListener("click", () => { finish(); });
    const help = $("help-tour");
    if (help) help.addEventListener("click", () => { endTour(); open("tour"); });
    document.addEventListener("studio:open-help", () => { endTour(); open("tour"); });
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (touring) { finish(); return; }
      if (!$("wizard").hidden) finish();
    });
    window.addEventListener("resize", () => { if (touring && tourSpot) positionCard($("tour-card"), tourSpot); });
    window.WizardUI = Object.freeze({
      open,
      openTour: () => { endTour(); open("tour"); },
      startTour,
      finish,
      isActive,
    });
    if (!automatedSession() && !storage.get(SETUP_KEY)) open("welcome");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
  else wire();
})();

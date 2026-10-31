/* SPDX-License-Identifier: MIT */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const form = $('form');
  const urls = new Map();
  let epoch = 0, job = null, busy = false, timer = null, controller = new AbortController();
  let selectedWorkflow = 'recast-room';
  let archiveVersion = 0;
  let health = null, healthVersion = 0, recommended = false, running = false;
  const isCurrent = (version, id = job) => version === epoch && id === job;
  const setStep = (step) => document.querySelectorAll('[data-step]').forEach((item) => {
    if (item.dataset.step === step) item.setAttribute('aria-current', 'step');
    else item.removeAttribute('aria-current');
  });
  const errorText = (value) => typeof value === 'string' ? value : Array.isArray(value)
    ? value.map((item) => item.msg || 'Invalid input').join('; ') : 'The server could not complete this request.';
  class APIError extends Error {
    constructor(message, status, detail, provesNoSubmission = false, beforeRequest = false) {
      super(message);
      this.status = status;
      this.detail = detail;
      this.provesNoSubmission = provesNoSubmission;
      this.beforeRequest = beforeRequest;
    }
  }
  const publicMessage = (value) => {
    if (typeof value === 'string') return value;
    if (value && typeof value === 'object') {
      if (value.message || value.msg) return String(value.message || value.msg);
      if (value.error) return publicMessage(value.error);
    }
    return 'The server could not complete this request.';
  };
  const detailMessage = (payload, fallback) => {
    const detail = payload?.detail || payload?.message || fallback;
    return Array.isArray(detail) ? errorText(detail) : publicMessage(detail);
  };
  async function request(path, options = {}) {
    const response = await fetch(path, { ...options, signal: controller.signal });
    let payload;
    try { payload = await response.json(); } catch (_) { throw new APIError(`Server response unreadable (${response.status}). Check the connection and retry.`, response.status); }
    if (!response.ok) {
      const detail = payload?.detail;
      const guardedLegacyRefusal = response.status === 503
        && typeof detail === 'object' && detail !== null && !Array.isArray(detail)
        && typeof detail.code === 'string' && detail.code.startsWith('renderer_')
        && typeof detail.message === 'string';
      const guardedSdkRefusal = response.status === 503
        && typeof detail?.error === 'object' && detail.error !== null
        && typeof detail.error.code === 'string'
        && typeof detail.error.message === 'string';
      const guardedSdkStateRefusal = response.status === 409
        && detail?.code === 'SDK_SUBMISSION_OUTCOME_UNKNOWN'
        && typeof detail?.message === 'string';
      const refusalDetail = guardedSdkRefusal ? detail.error : detail;
      throw new APIError(
        publicMessage(refusalDetail) || `Request failed (${response.status})`,
        response.status,
        detail,
        guardedLegacyRefusal || guardedSdkRefusal || guardedSdkStateRefusal,
      );
    }
    return payload;
  }
  const isLegacy = (payload = health) => payload?.backend === 'legacy';
  const runConnectionReady = (payload = health) => {
    if (!payload?.ok) return false;
    if (payload.backend === 'dry_run') return true;
    if (isLegacy(payload)) return payload.renderer_ready === true;
    if (payload.backend === 'sdk') return payload.configuration_ready === true;
    return false;
  };
  const rendererMessage = (payload = health) => payload?.renderer?.message || 'The Comfy connection is not configured. Check it again.';
  function readinessStates() {
    const hasSource = Boolean($('source').files.length);
    const savedReferences = window.ProjectsUI?.getReferenceState?.();
    const hasReference = Boolean($('reference_1').files.length || savedReferences?.ready);
    const hasRights = $('rights').checked;
    const customWorkflow = Boolean($('workflow').files.length);
    const connectionReady = Boolean(health?.ok && runConnectionReady(health));
    return {
      source: busy
        ? { state: 'checking', label: 'Inspecting source' }
        : !hasSource
          ? { state: 'blocked', label: 'Not selected' }
          : job && recommended
            ? { state: 'ok', label: 'Preflight passed' }
            : job
              ? { state: 'warning', label: 'Preflight warning' }
              : { state: 'pending', label: 'Selected · preflight pending' },
      reference: hasReference
        ? { state: 'pending', label: savedReferences?.ready ? 'Saved version selected' : 'Selected' }
        : { state: 'blocked', label: 'Missing' },
      rights: hasRights
        ? { state: 'ok', label: 'Permission recorded' }
        : { state: 'blocked', label: 'Permission required' },
      workflow: busy
        ? { state: 'checking', label: 'Validating workflow' }
        : !health
          ? { state: 'unknown', label: 'Checking' }
          : !health.workflow_exists
            ? { state: 'blocked', label: 'Workflow missing' }
            : customWorkflow
              ? { state: 'pending', label: 'Custom workflow pending validation' }
              : { state: 'ok', label: 'Bundled workflow ready' },
      renderer: !health
        ? { state: 'unknown', label: 'Checking' }
        : health.backend === 'dry_run'
          ? { state: 'ok', label: 'Preview runner ready' }
          : isLegacy() && health.renderer_ready === true
            ? { state: 'ok', label: 'Renderer reachable' }
            : isLegacy()
              ? { state: 'blocked', label: 'ComfyUI disconnected' }
              : health.configuration_ready === true
                ? { state: 'pending', label: 'Hosted Comfy configured · reachability unchecked' }
                : { state: 'blocked', label: 'Hosted Comfy configuration incomplete' },
      execution: !health
        ? { state: 'unknown', label: 'Checking' }
        : health.backend === 'dry_run'
          ? { state: 'ok', label: 'Preview · no AI inference' }
          : job && !recommended
            ? { state: 'blocked', label: 'Blocked by preflight' }
            : !connectionReady && health.backend === 'legacy'
              ? { state: 'blocked', label: 'Blocked until ComfyUI answers' }
              : !connectionReady
                ? { state: 'blocked', label: 'Blocked until SDK configuration is complete' }
              : job
                ? { state: 'ok', label: 'H3 run ready' }
                : { state: 'pending', label: 'Hosted Comfy configured' },
    };
  }
  function updateReadiness() {
    const states = readinessStates();
    document.querySelectorAll('#readiness [data-readiness]').forEach((node) => {
      const item = states[node.dataset.readiness];
      if (!item) return;
      node.dataset.state = item.state;
      const description = node.querySelector('dd');
      if (description) description.textContent = item.label;
    });
  }
  function controls() {
    const savedReferences = window.ProjectsUI?.getReferenceState?.();
    const ready = $('source').files.length
      && ($('reference_1').files.length || Boolean(savedReferences?.ready)) && $('rights').checked;
    $('submit').disabled = !ready || busy || !health?.ok || !health?.workflow_exists;
    $('submit').textContent = busy ? 'Working…' : job ? 'Prepare a new job ↗' : 'Prepare workflow ↗';
    $('prepare-help').textContent = busy ? 'Wait for this request, or reset to start over.' : !health?.ok
      ? 'Connection not verified. Check it before preparing.' : !health.workflow_exists
      ? 'The server workflow is missing. Restore the repository workflow.' : !ready
      ? 'Select a source and primary reference, then confirm permission.' : 'Ready for preflight. Your media will upload when you prepare.';
    $('run').disabled = !job || !recommended || busy || running || !runConnectionReady();
    $('run-help').textContent = running ? 'A run may be in progress. Check status before submitting again.' : !job
      ? 'Preparation must finish before running.' : !recommended ? 'Source preflight did not recommend this clip. Choose another source and prepare again.'
      : !health?.ok ? 'Connection unknown. Check it before running.' : isLegacy() && health.renderer_ready === undefined
      ? 'Checking the ComfyUI connection before running…' : isLegacy() && health.renderer_ready !== true
      ? `${rendererMessage()} Prepared files and permissions are preserved.` : health.backend === 'dry_run'
      ? 'Preview only: copies source media. No AI inference or recasting.' : health.backend === 'sdk' && health.configuration_ready !== true
      ? `${rendererMessage()} Prepared files and permissions are preserved.` : 'Runs the configured service. Hosted execution may incur provider charges.';
    updateReadiness();
  }
  function clearVideo(id) { const video = $(id); video.pause(); video.removeAttribute('src'); video.load(); }
  function invalidate() {
    epoch += 1; controller.abort(); controller = new AbortController(); clearTimeout(timer);
    job = null; busy = false; running = false; recommended = false;
    $('result').hidden = true; $('review').hidden = true; $('error').hidden = true;
    $('retry-status').hidden = true; $('downloads').replaceChildren(); $('prepared-links').replaceChildren();
    $('run-contract').hidden = true; $('prepared-contract-facts').replaceChildren();
    $('prepared-word-schedule').textContent = '';
    $('sdk-recovery').hidden = true; $('sdk-recovery-facts').replaceChildren();
    $('sdk-recovery-guidance').textContent = '';
    clearVideo('final-preview'); clearVideo('comparison-preview'); setStep('upload'); controls();
  }
  function preview(id) {
    const media = $(`${id}-preview`), file = $(id).files[0];
    if (id === 'source') clearVideo('source-preview'); else media.removeAttribute('src');
    if (urls.has(id)) URL.revokeObjectURL(urls.get(id));
    urls.delete(id); media.hidden = !file; $(`${id}-empty`).hidden = !!file;
    if (file) { const url = URL.createObjectURL(file); urls.set(id, url); media.src = url; }
  }
  function showError(message) { $('error').textContent = message; $('error').hidden = false; }
  function selectWorkflow(id, note) {
    selectedWorkflow = id;
    document.querySelectorAll('[data-workflow-id]').forEach((card) => {
      const current = card.dataset.workflowId === id;
      card.classList.toggle('selected', current);
      card.setAttribute('aria-current', current ? 'true' : 'false');
    });
    $('workflow-note').textContent = note;
    if (id === 'custom-recast') {
      $('advanced').open = true;
      $('workflow').focus();
    }
  }
  async function loadCatalog() {
    try {
      const payload = await request('/api/workflows');
      // The default workspace shows only workflows that can run in this release.
      // Future lanes remain documented in README/ROADMAP without cluttering setup.
      const cards = (payload.workflows || []).filter((item) => item.available === true);
      $('workflow-catalog').replaceChildren(...cards.map((item) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = `workflow-card status-${String(item.status).toLowerCase()}`;
        card.dataset.workflowId = item.id;
        card.disabled = !item.available;
        const heading = document.createElement('strong');
        heading.textContent = item.name;
        const summary = document.createElement('span');
        summary.textContent = item.summary;
        const model = document.createElement('small');
        model.textContent = `${item.status} · ${item.model}`;
        const badges = document.createElement('span');
        badges.className = 'badges';
        badges.textContent = (item.badges || []).join(' · ');
        card.append(heading, summary, model, badges);
        card.addEventListener('click', () => selectWorkflow(
          item.id,
          item.available
            ? `${item.name}: ${item.description}`
            : `${item.name} is a visible concept lane, not a ready workflow in this release.`,
        ));
        return card;
      }));
      selectWorkflow(selectedWorkflow, 'Recast Room selected.');
    } catch (_) {
      $('workflow-catalog').replaceChildren();
      $('workflow-note').textContent = 'Workflow catalog unavailable. The Recast Room remains active.';
    }
  }
  function moveAdvancedPanels() {
    const container = $('advanced-studio-panels');
    const panels = document.querySelectorAll('.projects-shell');
    if (!container || !panels.length) return;
    container.append(...panels);
  }
  const SETUP_KEY = 'recastroom-setup-v1';
  const COLLAB_KEY = 'recastroom-collab-v1';
  const RUNTIME_BACKENDS = { preview: 'dry_run', comfyui: 'legacy', 'comfy-sdk': 'sdk' };
  const RUNTIME_COMMANDS = {
    preview: 'RECASTROOM_BACKEND=dry_run ./run.sh',
    comfyui: 'RECASTROOM_BACKEND=legacy RECASTROOM_COMFY_URL=http://127.0.0.1:8188 ./run.sh',
    'comfy-sdk': 'RECASTROOM_BACKEND=sdk COMFY_API_KEY=<your-key> COMFY_BASE_URL=https://<deployment>.run.comfy.app COMFY_SDK_ASSET_BRIDGE=openjutsu-v1 ./run.sh',
  };
  let walkthroughStep = 0;
  function selectedRadio(name) {
    return document.querySelector(`input[name="${name}"]:checked`)?.value || '';
  }
  function updateCollabStatus() {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(COLLAB_KEY) || 'null'); } catch (_) { saved = null; }
    const status = $('collab-status');
    if (!saved || saved.mode === 'solo') { status.hidden = true; status.textContent = ''; return; }
    status.hidden = false;
    status.textContent = saved.reviewer ? `REVIEW HANDOFF · ${saved.reviewer}` : 'REVIEW HANDOFF';
  }
  function savedSetupPreference() {
    try { return JSON.parse(localStorage.getItem(SETUP_KEY) || 'null'); } catch (_) { return null; }
  }
  function updateConnectionGuidance() {
    const card = $('runtime-setup'), message = $('runtime-setup-message'), command = $('runtime-command');
    const selected = savedSetupPreference()?.connection;
    if (!health || !selected || !(selected in RUNTIME_BACKENDS) || health.backend === RUNTIME_BACKENDS[selected]) {
      card.hidden = true;
      message.textContent = '';
      command.textContent = '';
      return;
    }
    message.textContent = `Selected ${selected}, but the server is running ${health.backend}. Restart with the matching mode.`;
    command.textContent = RUNTIME_COMMANDS[selected];
    card.hidden = false;
  }
  function closeWalkthrough() {
    $('walkthrough').hidden = true;
    $('show-walkthrough').focus();
  }
  function openWalkthrough() {
    setWalkthroughStep(0);
    $('walkthrough').hidden = false;
    $('walkthrough-next').focus();
  }
  function setWalkthroughStep(step) {
    walkthroughStep = step;
    document.querySelectorAll('[data-walkthrough-step]').forEach((panel) => {
      panel.hidden = Number(panel.dataset.walkthroughStep) !== step;
    });
    document.querySelectorAll('#walkthrough-progress li').forEach((item, index) => {
      item.classList.toggle('current', index === step);
      item.classList.toggle('done', index < step);
      item.querySelector('span').textContent = index < step ? '✓' : String(index + 1);
    });
    $('walkthrough-back').hidden = step === 0;
    $('walkthrough-skip').hidden = step === 4;
    $('walkthrough-skip').textContent = step === 0 ? 'Skip setup' : 'Skip';
    $('walkthrough-next').hidden = step === 4;
    $('walkthrough-finish').hidden = step !== 4;
    $('walkthrough-next').textContent = step === 0 ? 'Start' : step === 3 ? 'Review setup' : 'Next';
  }
  function finishWalkthrough() {
    const preferences = {
      connection: selectedRadio('walkthrough-connection'),
      studio: selectedRadio('walkthrough-studio'),
      collab: selectedRadio('walkthrough-collab'),
      reviewer: $('walkthrough-reviewer').value.trim(),
      completedAt: new Date().toISOString(),
    };
    try {
      localStorage.setItem(SETUP_KEY, JSON.stringify(preferences));
      localStorage.setItem(COLLAB_KEY, JSON.stringify({mode: preferences.collab, reviewer: preferences.reviewer}));
    } catch (_) { /* Private mode still allows the current session setup. */ }
    if (preferences.studio === 'advanced') $('advanced-studio').open = true;
    else $('advanced-studio').open = false;
    updateCollabStatus();
    updateConnectionGuidance();
    closeWalkthrough();
    guideTo('source');
  }
  function skipWalkthrough() {
    if (walkthroughStep === 0) {
      const preferences = {
        connection: selectedRadio('walkthrough-connection'),
        studio: selectedRadio('walkthrough-studio'),
        collab: selectedRadio('walkthrough-collab'),
        reviewer: $('walkthrough-reviewer').value.trim(),
        completedAt: new Date().toISOString(),
        skipped: true,
      };
      try {
        localStorage.setItem(SETUP_KEY, JSON.stringify(preferences));
        localStorage.setItem(COLLAB_KEY, JSON.stringify({mode: preferences.collab, reviewer: preferences.reviewer}));
      } catch (_) { /* Private mode still allows setup to be skipped for this page view. */ }
      updateConnectionGuidance();
      closeWalkthrough();
      return;
    }
    setWalkthroughStep(Math.min(4, walkthroughStep + 1));
  }
  function guideTo(id) {
    if (!$('walkthrough').hidden) return;
    const target = $(id);
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.focus({ preventScroll: true });
  }
  function addLink(container, href, label, filename) {
    const link = document.createElement('a'); link.href = href; link.textContent = label;
    if (filename) link.download = filename;
    $(container).append(link);
  }
  function updateReviewLanguage(status) {
    const preview = status.backend === 'dry_run' || status.presentation === 'preview';
    $('final-caption').textContent = preview
      ? 'Preview copy · no AI inference'
      : 'Final · original audio restored';
    $('comparison-caption').textContent = preview
      ? 'Source / preview copy · paired review'
      : 'Source / final · paired review';
  }
  function renderFactList(container, facts) {
    $(container).replaceChildren(...facts.map(([label, value]) => {
      const item = document.createElement('div');
      const name = document.createElement('dt');
      name.textContent = label;
      const detail = document.createElement('dd');
      detail.textContent = value;
      item.append(name, detail);
      return item;
    }));
  }
  function renderPreparedContract(contract) {
    if (!contract) return;
    const treatment = contract.source_treatment || {};
    renderFactList('prepared-contract-facts', [
      ['Source file', contract.source || 'Not routed'],
      ['Primary reference', contract.reference_1 || 'Not routed'],
      ['Second reference', contract.reference_2 || 'Not supplied'],
      ['Seed', String(contract.seed ?? 'Unknown')],
      ['Scheduler steps', String(contract.steps ?? 'Unknown')],
      ['Character swap strength', String(contract.character_swap_strength ?? 'Unknown')],
      ['Audio conditioning', contract.audio_conditioning === true ? 'Attached to H3' : 'Not attached'],
      ['Source treatment', `${treatment.blur || 'Unset'} · ${treatment.effect || 'Unset'} · strength ${treatment.strength ?? 'Unknown'}`],
      ['Timing', `${contract.timing?.status || 'Unknown'} · ${contract.timing?.basis || 'Unknown basis'}`],
      ['Graph nodes', `planner ${contract.nodes?.planner} · conditioning ${contract.nodes?.conditioning} · output ${contract.nodes?.output}`],
    ]);
    $('prepared-word-schedule').textContent = contract.timing?.schedule || 'No schedule was embedded in the prompt.';
    $('run-contract').hidden = false;
  }
  function renderSdkSubmission(status) {
    const shouldShow = status?.backend === 'sdk' || Boolean(status?.sdk_phase);
    $('sdk-recovery').hidden = !shouldShow;
    if (!shouldShow) return;
    const retry = status.retry || 'unknown';
    renderFactList('sdk-recovery-facts', [
      ['Local phase', status.sdk_phase ? String(status.sdk_phase) : 'No durable submission yet'],
      ['Provider job ID', status.provider_job_id ? String(status.provider_job_id) : 'Not recorded'],
      ['Retry policy', retry],
    ]);
    $('sdk-recovery-guidance').textContent = retry === 'blocked'
      ? 'SDK outcome is unknown. Do not start a new submission; reconcile the recorded state first.'
      : retry === 'resume'
        ? 'A provider job ID is recorded. A retry should resume that submission rather than create a duplicate.'
        : retry === 'allowed'
          ? 'No prior provider submission is recorded for this prepared job.'
          : 'SDK recovery state is unavailable. Check status before retrying.';
  }
  async function loadRecordedProof() {
    try {
      const proof = await request('/api/proof/comfy-api-sdk-c1');
      $('proof-job').textContent = proof.job_id;
      $('proof-status').textContent = proof.status;
      $('proof-output').textContent = `${proof.format.width}×${proof.format.height} · ${proof.format.duration_seconds}s · SHA-256 ${proof.output_sha256.slice(0, 12)}…`;
      $('proof-audio').textContent = 'Source and final decoded PCM match exactly';
      $('proof-comparison').src = proof.media.comparison;
      $('recorded-proof').hidden = false;
    } catch (_) {
      $('proof-summary').textContent = 'The recorded hosted proof is unavailable here. It remains available in the repository evidence.';
      $('recorded-proof').hidden = false;
    }
  }
  async function searchArchive(version = ++archiveVersion) {
    const query = $('archive-query').value.trim();
    const results = $('archive-results'), note = $('archive-note');
    results.replaceChildren(); note.textContent = query ? 'Searching Archive.org…' : 'Enter a search term first.';
    if (!query) return;
    try {
      const payload = await request(`/api/archive/sources?${new URLSearchParams({ query, limit: '6' })}`);
      if (version !== archiveVersion) return;
      if (!payload.result_count) { note.textContent = 'No matching items returned.'; return; }
      note.textContent = `${payload.result_count} result${payload.result_count === 1 ? '' : 's'} · ${payload.provider} · no API key`;
      results.replaceChildren(...(payload.sources || []).map((item) => {
        const row = document.createElement('li');
        const link = document.createElement('a');
        link.href = item.details_url; link.target = '_blank'; link.rel = 'noopener noreferrer';
        link.textContent = item.title;
        const rights = document.createElement('small');
        rights.textContent = item.rights?.public_domain
          ? `explicit public-domain license · ${item.identifier}`
          : `rights review required · ${item.identifier}`;
        row.append(link, rights); return row;
      }));
    } catch (error) {
      if (version === archiveVersion) note.textContent = `Archive search unavailable: ${error.message}`;
    }
  }
  async function checkHealth() {
    const version = ++healthVersion;
    health = null; controls(); $('backend').textContent = 'Connection unknown · checking';
    try {
      const response = await fetch('/api/health');
      if (!response.ok) throw new Error('unavailable');
      const payload = await response.json();
      if (version !== healthVersion) return;
      health = payload;
      $('backend').textContent = payload.ok ? payload.backend === 'dry_run'
        ? 'PREVIEW · No AI inference · source-copy output'
        : isLegacy(payload) ? payload.renderer_ready === true
          ? 'ComfyUI connected · model, cost, and location not verified'
          : `ComfyUI disconnected · ${publicMessage(payload.renderer)}`
        : payload.configuration_ready === true
          ? 'Hosted Comfy configured · reachability unchecked · cost and location not verified'
          : `Hosted Comfy incomplete · ${publicMessage(payload.renderer)}`
        : 'Connection unavailable';
    } catch (_) { if (version !== healthVersion) return; $('backend').textContent = 'Connection unavailable'; }
    updateConnectionGuidance();
    $('health-retry').hidden = Boolean(health?.ok && runConnectionReady(health)); controls();
    return health;
  }
  form.addEventListener('input', (event) => {
    if (event.target.closest('#archive-panel')) return;
    invalidate();
    // A changed media selection needs a new, manual permission confirmation.
    if (['source', 'reference_1', 'reference_2'].includes(event.target.id)) {
      $('rights').checked = false; preview(event.target.id); controls();
    }
    if (event.target.id === 'workflow') {
      $('rights').checked = false; controls();
      $('workflow-note').textContent = event.target.files.length
        ? `Custom workflow selected: ${event.target.files[0].name}. It must pass server validation.`
        : 'Custom workflow cleared. The bundled RecastRoom workflow will be used.';
    }
  });
  document.addEventListener('projects:selection-change', () => {
    // Do not abort startup catalog/health probes when no prepared result exists.
    if (job || busy || running) invalidate();
    // Saved and uploaded references are alternatives; either change needs fresh consent.
    $('rights').checked = false;
    preview('reference_1'); preview('reference_2'); controls();
  });
  $('source-preview').addEventListener('error', () => { $('source-note').textContent = 'Browser preview unavailable for this file. Try an MP4, or let server preflight inspect it.'; });
  $('source-preview').addEventListener('loadedmetadata', () => { $('source-note').textContent = 'Preview ready. Inspect your source before preparing.'; });
  $('archive-search').addEventListener('click', () => { searchArchive(); });
  $('archive-query').addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); searchArchive(); } });
  $('reset').addEventListener('click', () => {
    HTMLFormElement.prototype.reset.call(form); invalidate(); ['source', 'reference_1', 'reference_2'].forEach(preview);
    selectedWorkflow = 'recast-room'; selectWorkflow(selectedWorkflow, 'Recast Room selected.');
    document.dispatchEvent(new CustomEvent('studio:reset'));
    $('source-note').textContent = 'MP4, MOV or MKV. Some formats may not preview in your browser.';
    $('source').focus();
  });
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if ($('submit').disabled || !form.reportValidity()) return;
    invalidate(); const version = epoch;
    busy = true; $('result').hidden = false; $('stage').textContent = 'PREPARING';
    $('job-label').textContent = 'PREFLIGHT'; $('output').textContent = 'Uploading your selections and inspecting the source…';
    setStep('prepare'); controls();
    const data = new FormData(form); data.set('rights_attested', String($('rights').checked));
    for (const name of ['project_id', 'character_id', 'character_version', 'reference_2', 'words', 'workflow']) {
      const value = data.get(name);
      if (value === '' || (value instanceof File && !value.name)) data.delete(name);
    }
    try {
      const payload = await request('/api/prepare', { method: 'POST', body: data });
      if (!isCurrent(version, null)) return;
      if (!/^[a-zA-Z0-9]{8,32}$/.test(payload.job_id || '')) throw new Error('Server returned an invalid job ID. Prepare again.');
      job = payload.job_id; recommended = payload.scene?.recommended === true;
      $('stage').textContent = 'PREPARED'; $('job-label').textContent = `JOB / ${job}`;
      $('output').textContent = recommended ? 'Preflight recommends this source. Your workflow is prepared; nothing has been generated yet.' : 'Workflow prepared, but this source did not pass the recommendation check. Replace the clip before running.';
      addLink('prepared-links', `/api/jobs/${job}/workflow`, 'Workflow JSON');
      addLink('prepared-links', `/api/jobs/${job}/prompt`, 'Prompt'); setStep('run');
      renderPreparedContract(payload.contract);
      document.dispatchEvent(new CustomEvent('projects:prepared', {detail: payload}));
    } catch (error) { if (version === epoch) { $('stage').textContent = 'PREPARATION STOPPED'; $('output').textContent = 'No runnable job was prepared.'; showError(`Could not prepare: ${error.message} Check your media and timing JSON, then prepare again.`); } }
    finally { if (version === epoch) { busy = false; controls(); } }
  });
  async function poll(version, id) {
    if (!isCurrent(version, id)) return;
    clearTimeout(timer); $('retry-status').hidden = true;
    try {
      const status = await request(`/api/jobs/${id}/status`);
      if (!isCurrent(version, id)) return;
      $('error').hidden = true;
      $('stage').textContent = String(status.state || 'unknown').toUpperCase();
      $('output').textContent = String(status.message || 'Waiting for a server update.');
      renderSdkSubmission(status);
      if (status.state === 'complete' && status.backend === 'dry_run') $('output').textContent = 'Preview complete · no AI inference or recasting · output copies the source.';
      if (status.state === 'complete') {
        running = false; busy = false; $('review').hidden = false; $('downloads').replaceChildren();
        updateReviewLanguage(status);
        const preview = status.backend === 'dry_run' || status.presentation === 'preview';
        const names = preview
          ? { generated: 'Preview source copy', final: 'Preview copy', side_by_side: 'Source / preview comparison' }
          : { generated: 'Generated clip', final: 'Final with audio', side_by_side: 'Side-by-side review' };
        for (const key of Object.keys(names)) {
          if (!status.artifacts?.[key]) continue;
          const path = `/api/jobs/${id}/artifacts/${key}`;
          addLink('downloads', path, `Download ${names[key]}`, `${id}-${key}.mp4`);
          if (key === 'final') $('final-preview').src = path;
          if (key === 'side_by_side') $('comparison-preview').src = path;
        }
        setStep('review'); controls();
      } else if (status.state === 'error') {
        busy = false; running = false;
        const blockedOutcome = status.retry === 'blocked';
        showError(`Run stopped: ${errorText(status.error?.message || status.message)} ${blockedOutcome ? 'SDK outcome is unknown; do not start another submission.' : 'Check the configured service, then retry the run or reset.'}`); controls();
      } else { timer = setTimeout(() => poll(version, id), 1500); }
    } catch (error) {
      if (!isCurrent(version, id)) return;
      busy = false; running = true;
      showError(`Status unavailable: ${error.message} The server job may still be running. Check status again; do not submit a duplicate run.`);
      $('retry-status').hidden = false; controls();
    }
  }
  $('run').addEventListener('click', async () => {
    if ($('run').disabled) return;
    const version = epoch, id = job; busy = true;
    $('error').hidden = true; $('review').hidden = true; $('downloads').replaceChildren();
    clearVideo('final-preview'); clearVideo('comparison-preview');
    $('stage').textContent = 'CHECKING'; $('output').textContent = 'Checking the configured ComfyUI connection before submission…'; controls();
    try {
      const verifiedHealth = await checkHealth();
      if (!isCurrent(version, id)) return;
      if (!runConnectionReady(verifiedHealth)) {
        throw new APIError(rendererMessage(verifiedHealth), 503, verifiedHealth?.renderer, true, true);
      }
      running = true;
      $('stage').textContent = 'SUBMITTING'; $('output').textContent = 'Requesting a run from the configured service…'; controls();
      await request(`/api/jobs/${id}/run`, { method: 'POST' });
      if (!isCurrent(version, id)) return;
      await poll(version, id);
    } catch (error) {
      if (!isCurrent(version, id)) return;
      busy = false;
      if (error.provesNoSubmission) {
        running = false;
        const detail = error.detail?.error && typeof error.detail.error === 'object'
          ? error.detail.error
          : error.detail && typeof error.detail === 'object' ? error.detail : null;
        if (detail?.code || detail?.message) health = { ...health, renderer_ready: false, renderer: detail };
        $('backend').textContent = health?.backend === 'sdk'
          ? `Hosted Comfy incomplete · ${publicMessage(detail)}`
          : `ComfyUI disconnected · ${publicMessage(detail)}`;
        $('stage').textContent = 'RUN BLOCKED';
        $('output').textContent = error.beforeRequest
          ? 'No run request was sent. Prepared files and permissions are preserved.'
          : 'The server refused the run before queueing or uploading. Prepared files and permissions are preserved.';
        const variable = detail?.environment_variable ? ` Set ${detail.environment_variable}, then restart in the matching mode.` : '';
        showError(`${error.beforeRequest ? 'Run not submitted:' : 'Run refused:'} ${publicMessage(detail)}${variable} Check the connection again, then run without preparing a new job.`);
        $('retry-status').hidden = true; $('health-retry').hidden = false; controls();
      } else {
        showError(`Run confirmation unavailable: ${error.message} Check status first in case the request reached the server. If no job exists, prepare a new job.`);
        $('retry-status').hidden = false; controls();
      }
    }
  });
  $('retry-status').addEventListener('click', () => { if (job) poll(epoch, job); });
  $('health-retry').addEventListener('click', checkHealth);
  $('copy-runtime-command').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('runtime-command').textContent);
      $('copy-runtime-command').textContent = 'Command copied';
    } catch (_) {
      $('copy-runtime-command').textContent = 'Copy failed · select command';
    }
    setTimeout(() => { $('copy-runtime-command').textContent = 'Copy launch command'; }, 1800);
  });
  $('show-walkthrough').addEventListener('click', openWalkthrough);
  $('hero-walkthrough').addEventListener('click', openWalkthrough);
  $('walkthrough-skip').addEventListener('click', skipWalkthrough);
  $('walkthrough-back').addEventListener('click', () => setWalkthroughStep(Math.max(0, walkthroughStep - 1)));
  $('walkthrough-next').addEventListener('click', () => setWalkthroughStep(Math.min(4, walkthroughStep + 1)));
  $('walkthrough-finish').addEventListener('click', finishWalkthrough);
  document.querySelectorAll('[data-guide-target]').forEach((button) => {
    button.addEventListener('click', () => guideTo(button.dataset.guideTarget));
  });
  $('walkthrough').addEventListener('click', (event) => {
    // Required first-run setup cannot be dismissed by clicking the backdrop.
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !$('walkthrough').hidden) event.preventDefault();
  });
  window.addEventListener('beforeunload', () => { controller.abort(); clearTimeout(timer); urls.forEach((url) => URL.revokeObjectURL(url)); });
  // Small, read-only seams for the dependent frontend regression story.
  window.StudioUI = Object.freeze({
    errorText,
    getReadiness: readinessStates,
    renderPreparedContract,
    renderSdkSubmission,
    getState: () => ({ epoch, jobId: job, busy, running, recommended, backend: health?.backend || null, rendererReady: runConnectionReady() }),
    closeWalkthrough,
    finishWalkthrough,
    openWalkthrough,
  });
  moveAdvancedPanels();
  loadRecordedProof();
  updateCollabStatus();
  let completedSetup = null;
  try { completedSetup = JSON.parse(localStorage.getItem(SETUP_KEY) || 'null'); } catch (_) { completedSetup = null; }
  if (!completedSetup) openWalkthrough();
  else if (completedSetup.studio === 'advanced') $('advanced-studio').open = true;
  loadCatalog();
  checkHealth();
})();

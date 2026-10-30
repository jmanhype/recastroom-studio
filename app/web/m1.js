/* SPDX-License-Identifier: MIT */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  let requestEpoch = 0;
  let sourceTiming = null;
  let wordTiming = null;
  let wordTimingError = false;
  let wordTimingEpoch = 0;
  let scenes = [];
  let profiles = [];
  let resolvedOperation = null;
  let attempts = [];
  let authorizedAttemptId = null;
  let authorizedRequestKey = null;
  let attemptEpoch = 0;
  let takes = [];
  let selectedTakeId = null;
  let challengerIncumbentTakeId = null, challengerAttemptId = null, challengerRequestKey = null;
  let retainedReplayImport = null;
  let selectionRevision = 0;
  let exportTakes = {};
  let editRevision = null;
  let exportRecord = null;
  const responseFacts = Symbol('response facts');
  const isCurrent = (version) => version === requestEpoch;
  const isAttemptCurrent = (version) => version === attemptEpoch;
  const message = (value, fallback) => {
    if (typeof value === 'string') return value;
    if (Array.isArray(value)) return value.map((item) => item?.msg || 'Invalid input').join('; ');
    if (value && typeof value === 'object') return String(value.message || value.msg || fallback);
    return fallback;
  };
  function element(tag, options = {}, children = []) {
    const node = document.createElement(tag);
    Object.assign(node, options);
    node.append(...children.filter(Boolean));
    return node;
  }
  function buildResolutionPanel() {
    const section = element('section', {'aria-labelledby': 'm1-resolve-heading'});
    const list = $('m1-scenes').closest('.projects-grid');
    $('m1-scenes-heading').closest('section').querySelector('.hint').textContent =
      'Inspect and confirm exact original cuts, then review one pinned non-inference operation. Resolution never queues cost or generates media.';
    section.innerHTML = `<h3 id="m1-resolve-heading">Read-only settings review</h3>
      <label for="m1-profile">Saved workflow profile</label><select id="m1-profile"></select>
      <label for="m1-scene-select">Scene version</label><select id="m1-scene-select"></select>
      <label for="m1-shot-select">Original shot</label><select id="m1-shot-select"></select>
      <label for="m1-seed">Seed</label>
      <input id="m1-seed" type="number" min="0" step="1" value="117">
      <label for="m1-rights"><input id="m1-rights" type="checkbox"> I have permission for this source and reference</label>
      <button id="m1-resolve" type="button">Inspect prepared settings</button>
      <label for="m1-word-timing">Optional original-source word timing JSON</label>
      <input id="m1-word-timing" type="file" accept=".json,application/json">
      <button id="m1-word-clear" type="button">Clear word timing</button>
      <p id="m1-word-status" role="status">No word timing selected.</p>
      <p id="m1-resolve-note" class="hint" role="status">This review is read-only, never queues cost, and never starts generation.</p>
	    <dl id="m1-resolve-output" class="readiness-strip"></dl>
      <h3 id="m1-production-heading">Preview authorization</h3>
      <label for="m1-mode">Execution mode</label>
      <select id="m1-mode">
        <option value="dry_run" selected>Local preview · offline non-inference</option>
        <option value="retained_replay" disabled>Saved result · import below, no execution</option>
        <option value="comfy" disabled>ComfyUI · separate setup required</option>
        <option value="sdk" disabled>Hosted Comfy · separate setup required</option>
      </select>
      <label for="m1-authorize-rights"><input id="m1-authorize-rights" type="checkbox"> I explicitly authorize this one local preview attempt</label>
      <button id="m1-authorize" type="button" disabled>Authorize one preview</button>
      <label for="m1-incumbent-select">Same-shot incumbent take</label>
      <select id="m1-incumbent-select"></select>
      <label for="m1-challenger-rights"><input id="m1-challenger-rights" type="checkbox"> I explicitly authorize one alternate preview</label>
      <button id="m1-challenger-authorize" type="button" disabled>Authorize one alternate preview</button>
      <p id="m1-challenger-note" class="hint" role="status">Resolve a shot, then select one qualified take attached to that exact shot.</p>
      <button id="m1-cancel" type="button" disabled>Record cancellation request</button>
      <button id="m1-reconcile" type="button" disabled>Request reconciliation</button>
      <p id="m1-production-note" class="hint" role="status">Resolve an operation first. Authorization is the only submission boundary.</p>
      <ul id="m1-attempts" aria-live="polite"></ul>
      <h3 id="m1-retained-heading">Saved result import</h3>
      <label for="m1-replay-file">Saved result file</label>
      <input id="m1-replay-file" type="file" accept="video/*,.nut">
      <label for="m1-replay-receipt">Result receipt JSON</label>
      <input id="m1-replay-receipt" type="file" accept="application/json,.json">
      <button id="m1-replay-import" type="button" disabled>Import saved result</button>
      <p id="m1-replay-status" class="hint" role="status">Select one saved result file and its matching JSON receipt; import never queues execution.</p>
      <p id="m1-replay-lineage" class="hint" aria-live="polite"></p>
      <h3 id="m1-review-heading">Review and reversible selection</h3>
      <label for="m1-review-shot">Review shot</label><select id="m1-review-shot"></select>
      <ul id="m1-takes" aria-live="polite"></ul>
      <video id="m1-comparison-preview" controls playsinline preload="metadata" aria-label="Aligned source and candidate comparison"></video>
      <p id="m1-comparison-caption" class="hint">No candidate selected.</p>
      <label for="m1-review-verdict">Human review</label>
      <select id="m1-review-verdict"><option value="keeper">Accept</option><option value="needs_review">Needs review</option><option value="reject">Reject</option></select>
      <label for="m1-review-note">Review note</label>
      <input id="m1-review-note" type="text" maxlength="4000" placeholder="Required human review note">
      <button id="m1-review-append" type="button">Append review</button>
      <button id="m1-deselect" type="button">Deselect current take</button>
      <button id="m1-selection-refresh" type="button">Refresh selection state</button>
      <p id="m1-review-note-status" class="hint" role="status">Reviews append history; selection is explicit and reversible.</p>
      <h3 id="m1-export-heading">Fixed edit export</h3>
      <div id="m1-export-list" aria-live="polite"></div>
      <button id="m1-export-add" type="button">Add explicit edit item</button>
      <label for="m1-audio-policy">Audio policy</label>
      <select id="m1-audio-policy"><option value="source_edit_map">Follow the edit</option><option value="mute">Mute</option><option value="source_stream_copy">Copy original stream</option></select>
      <button id="m1-create-edit" type="button" disabled>Create fixed edit version</button>
      <button id="m1-export" type="button" disabled>Export result</button>
      <a id="m1-export-download" href="#" download hidden>Download export bytes</a>
      <p id="m1-export-status" class="hint" role="status">Select explicit takes and source ranges; edits may trim, repeat, omit, or reorder.</p>`;
    list.append(section);
  }
  async function requestJSON(path, options = {}) {
    let response;
    let payload = null;
    try {
      response = await fetch(path, options);
      payload = await response.json();
    } catch (_) {
      const error = new Error('Server response unavailable. Check the connection and retry.');
      error[responseFacts] = {status: response?.status ?? null, decoded: false};
      throw error;
    }
    if (!response.ok) {
      const error = new Error(message(payload?.detail, `Request failed (${response.status}).`));
      error[responseFacts] = {status: response.status, decoded: true};
      throw error;
    }
    return payload;
  }
  function setBusy(busy) {
    $('m1-upload').disabled = busy || !$('m1-source').files.length;
    $('m1-confirm').disabled = busy || !sourceTiming;
    $('m1-add-shot').disabled = busy || !sourceTiming;
    $('m1-resolve').disabled = busy || !$('m1-profile').value
      || !$('m1-scene-select').value || !$('m1-shot-select').value;
    $('m1-authorize').disabled = busy || !resolvedOperation || !$('m1-authorize-rights').checked
      || $('m1-mode').value !== 'dry_run';
    $('m1-challenger-authorize').disabled = busy || !selectedIncumbentTake()
      || !$('m1-challenger-rights').checked || $('m1-mode').value !== 'dry_run';
    $('m1-cancel').disabled = busy || !currentAttempt()
      || ['completed', 'failed', 'provider_confirmed_cancelled'].includes(currentAttempt()?.state);
    $('m1-reconcile').disabled = $('m1-cancel').disabled;
    $('m1-create-edit').disabled = busy || !selectedScene() || !$('m1-export-list').children.length;
    $('m1-export').disabled = busy || !editRevision;
    $('m1-replay-import').disabled = busy || !$('m1-replay-file').files.length
      || !$('m1-replay-receipt').files.length;
  }
  function renderSource() {
    const facts = $('m1-source-facts').children;
    if (!sourceTiming) {
      facts[0].lastElementChild.textContent = 'Not inspected';
      facts[1].lastElementChild.textContent = 'Not inspected';
      facts[2].lastElementChild.textContent = 'Not inspected';
      facts[3].lastElementChild.textContent = 'Not inspected';
      return;
    }
    facts[0].lastElementChild.textContent = String(sourceTiming.frame_count);
    facts[1].lastElementChild.textContent = `${sourceTiming.timebase.num}/${sourceTiming.timebase.den} seconds/tick`;
    facts[2].lastElementChild.textContent = sourceTiming.has_audio ? 'Present' : 'Absent';
    facts[3].lastElementChild.textContent = sourceTiming.sha256;
  }
  function shotRow(shot = {id: '', start: 0, end: 0, kind: 'render'}) {
    const row = document.createElement('div');
    row.className = 'archive-search';
    const id = document.createElement('input');
    id.type = 'text'; id.value = shot.id; id.placeholder = 'shot-id'; id.maxLength = 128;
    const start = document.createElement('input');
    start.type = 'number'; start.min = '0'; start.step = '1'; start.value = String(shot.start);
    const end = document.createElement('input');
    end.type = 'number'; end.min = '0'; end.step = '1'; end.value = String(shot.end);
    const kind = document.createElement('select');
    kind.append(new Option('Render', 'render'), new Option('Explicit pass-through', 'pass_through'));
    kind.value = shot.kind;
    const remove = document.createElement('button');
    remove.type = 'button'; remove.textContent = 'Remove';
    row.append(id, start, end, kind, remove);
    remove.addEventListener('click', () => {
      if ($('m1-shot-list').children.length > 1) row.remove();
    });
    $('m1-shot-list').append(row);
  }
  function resetShots(frameCount) {
    $('m1-shot-list').replaceChildren();
    shotRow({id: 'shot-1', start: 0, end: frameCount, kind: 'pass_through'});
  }
  function clearSceneSetup(notice = 'Select a saved project, then upload a CFR source.') {
    clearWordTiming();
    sourceTiming = null;
    scenes = [];
    resolvedOperation = null;
    attempts = [];
    authorizedAttemptId = null;
    authorizedRequestKey = null;
    takes = [];
    selectedTakeId = null;
    challengerIncumbentTakeId = challengerAttemptId = challengerRequestKey = null;
    retainedReplayImport = null;
    selectionRevision = 0;
    exportTakes = {};
    editRevision = null;
    exportRecord = null;
    $('m1-source').value = '';
    $('m1-replay-file').value = '';
    $('m1-replay-receipt').value = '';
    $('m1-shot-list').replaceChildren();
    renderSource();
    renderScenes();
    renderResolution();
    renderProduction();
    renderReview();
    renderExport();
    renderRetainedReplay();
    $('m1-source-note').textContent = notice;
    $('m1-cut-note').textContent = 'Use frame ranges that cover every original frame exactly once. Use pass-through for frames you do not want recast.';
    setBusy(false);
  }
  function renderScenes() {
    const list = $('m1-scenes');
    list.replaceChildren();
    if (!scenes.length) {
      const empty = document.createElement('li');
      empty.textContent = 'No confirmed scene revisions yet.';
      list.append(empty);
      return;
    }
    scenes.forEach((scene) => {
      const item = document.createElement('li');
      const heading = document.createElement('strong');
      heading.textContent = `Scene revision ${scene.revision} · ${scene.shots.length} shots`;
      const details = document.createElement('small');
      details.textContent = `${scene.source.sha256.slice(0, 12)}… · ${scene.shots.map((shot) => `${shot.id} ${shot.source_range.start}-${shot.source_range.end} ${shot.kind}`).join(' | ')}`;
      item.append(heading, details);
      list.append(item);
    });
  }

  function selectedScene() {
    return scenes.find((scene) => scene.id === $('m1-scene-select').value) || null;
  }

  function currentAttempt() {
    return attempts.find((attempt) => attempt.id === authorizedAttemptId) || null;
  }

  function selectedReviewShot() {
    const scene = selectedScene();
    return scene?.shots.find((shot) => shot.id === $('m1-review-shot').value) || null;
  }

  function eligibleIncumbentTakes() {
    if (!resolvedOperation) return [];
    return takes.filter((take) => take.project_id === resolvedOperation.project_id
      && take.scene_revision_id === resolvedOperation.scene_revision_id
      && take.shot_id === resolvedOperation.shot_id && take.qualified && take.attempt_id);
  }

  function selectedIncumbentTake() {
    return eligibleIncumbentTakes().find((take) => take.id === challengerIncumbentTakeId) || null;
  }

  function renderChallenger() {
    const select = $('m1-incumbent-select');
    const eligible = eligibleIncumbentTakes();
    select.replaceChildren(new Option('Select one exact-shot incumbent', ''));
    eligible.forEach((take) => select.append(new Option(
      `${take.id} · ${{dry_run: 'Local preview', retained_replay: 'Saved result'}[take.origin] || take.origin} · result ${take.attempt_id}`, take.id,
    )));
    if (!selectedIncumbentTake()) challengerIncumbentTakeId = null;
    select.value = challengerIncumbentTakeId || '';
    const note = !resolvedOperation ? 'Resolve a shot, then select one qualified take attached to that exact shot.'
      : (eligible.length ? `Incumbent ${challengerIncumbentTakeId || 'unselected'} is limited to the resolved scene and shot.`
        : 'No qualified incumbent with an attempt is attached to this exact shot.');
    $('m1-challenger-note').textContent = note;
  }

  function renderProduction() {
    const list = $('m1-attempts');
    list.replaceChildren();
    if (!resolvedOperation) {
      $('m1-production-note').textContent = 'Resolve and review one read-only operation before authorization.';
    } else if (!attempts.length) {
      $('m1-production-note').textContent = 'No attempt is authorized. Reads and resolution never submit.';
    }
    attempts.forEach((attempt) => {
      const item = document.createElement('li');
      const heading = document.createElement('strong');
      const modeLabel = {dry_run: 'Local preview', retained_replay: 'Saved result'}[attempt.mode] || attempt.mode;
      heading.textContent = `${modeLabel} · ${attempt.state}`;
      const detail = document.createElement('small');
      const cancelState = {
        prepared: 'Queued prevention: cancellation prevents submission.',
        ready: 'Queued prevention: cancellation prevents submission.',
        submitting: 'Uncertain boundary: cancellation intent is durable; no blind retry.',
        submitted: 'Pending/unsupported CPU cancellation; no refund is claimed.',
        running: 'Pending/unsupported CPU cancellation; no refund is claimed.',
        downloading: 'Pending/unsupported CPU cancellation; output remains authenticated.',
        reconcile_needed: 'Paused unknown outcome; reconciliation is required before any conclusion or retry.',
        cancel_requested: 'Pending/unsupported CPU cancellation; no refund is claimed.',
        provider_confirmed_cancelled: 'Provider-confirmed cancellation; no refund is claimed.',
        completed: 'Completed local preview and saved the result.',
        failed: 'Failed; protected evidence and terminal state are retained.',
      }[attempt.state] || 'Waiting for the sole worker.';
      detail.textContent = `${cancelState} Attempt ${attempt.id}`;
      item.append(heading, detail);
      const select = element('button', {type: 'button', textContent: 'Select attempt controls'});
      select.addEventListener('click', () => {
        authorizedAttemptId = attempt.id;
        setBusy(false);
      });
      item.append(select);
      list.append(item);
    });
    const current = currentAttempt();
    if (current?.state === 'completed') {
      $('m1-production-note').textContent = 'The preview file remains in protected project storage. Use the saved result record for review.';
    }
  }

  function renderReview() {
    const scene = selectedScene();
    const shotSelect = $('m1-review-shot');
    const previousShot = shotSelect.value;
    shotSelect.replaceChildren();
    (scene?.shots || []).forEach((shot) => shotSelect.append(new Option(shot.id, shot.id)));
    if ([...shotSelect.options].some((option) => option.value === previousShot)) {
      shotSelect.value = previousShot;
    }
    const shot = selectedReviewShot();
    const list = $('m1-takes');
    list.replaceChildren();
    if (!scene || !shot) {
      $('m1-comparison-caption').textContent = 'Select a scene and review shot.';
      renderChallenger();
      return;
    }
    if (!takes.length) {
      const empty = document.createElement('li');
      empty.textContent = 'No saved or preview candidates for this exact shot.';
      list.append(empty);
      renderChallenger();
      return;
    }
    takes.forEach((take) => {
      if (take.scene_revision_id !== scene.id || take.shot_id !== shot.id) return;
      const item = document.createElement('li');
      const heading = document.createElement('strong');
      const originLabel = {dry_run: 'Local preview', replay: 'Saved result'}[take.origin] || take.origin;
      heading.textContent = `${originLabel} · ${take.qualified ? 'review ready' : 'needs review'}`;
      const detail = document.createElement('small');
      detail.textContent = `${take.id} · output ${take.output.sha256.slice(0, 18)}…`;
      const canonical = element('a', {href: `/api/assets/${encodeURIComponent(take.output.asset_id)}`, textContent: 'Original saved file'});
      canonical.target = '_blank';
      const compare = element('button', {type: 'button', textContent: 'Compare synchronized'});
      const choose = element('button', {type: 'button', textContent: 'Select candidate'});
      compare.addEventListener('click', () => {
        selectedTakeId = take.id;
        $('m1-comparison-preview').src = `/api/projects/${encodeURIComponent(scene.project_id)}/takes/${encodeURIComponent(take.id)}/comparison`;
        $('m1-comparison-caption').textContent = `Comparison video: original frames ${shot.source_range.start}-${shot.source_range.end} | saved result files remain unchanged.`;
      });
      choose.addEventListener('click', () => selectCandidate(take.id));
      item.append(heading, detail, canonical, compare, choose);
      list.append(item);
    });
    renderChallenger();
  }

  async function refreshTakes() {
    const scene = selectedScene();
    const shot = selectedReviewShot();
    if (!scene || !shot) {
      takes = [];
      renderReview();
      return;
    }
    const version = ++requestEpoch;
    try {
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(scene.project_id)}/scene-revisions/${encodeURIComponent(scene.id)}/takes?shot_id=${encodeURIComponent(shot.id)}`,
      );
      if (!isCurrent(version)) return;
      takes = Array.isArray(payload) ? payload : [];
      renderReview();
    } catch (error) {
      if (isCurrent(version)) {
        takes = [];
        renderReview();
        $('m1-review-note-status').textContent = `Candidates unavailable: ${error.message}`;
      }
    }
  }

  async function selectCandidate(takeId = null) {
    const scene = selectedScene();
    const shot = selectedReviewShot();
    if (!scene || !shot) return;
    const expected = selectionRevision;
    $('m1-review-note-status').textContent = takeId
      ? `Applying expected revision ${expected} selection…`
      : `Applying expected revision ${expected} deselection…`;
    try {
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(scene.project_id)}/scene-revisions/${encodeURIComponent(scene.id)}/shots/${encodeURIComponent(shot.id)}/selection`,
        {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({take_id: takeId, expected_revision: expected}),
        },
      );
      selectionRevision = payload.revision;
      selectedTakeId = takeId;
      $('m1-review-note-status').textContent = `Durable selection revision ${payload.revision} recorded.`;
    } catch (error) {
      $('m1-review-note-status').textContent = `Selection conflict visible (${error.message}); prior selection was not clobbered.`;
    }
  }

  function summaryValue(value) {
    return value.length > 24 ? `${value.slice(0, 18)}…${value.slice(-6)}` : value;
  }

  function resetExportEditor() {
    editRevision = null;
    exportRecord = null;
    $('m1-export-list').replaceChildren();
    $('m1-export-download').hidden = true;
    $('m1-export-status').textContent = 'Select explicit takes and source ranges; edits may trim, repeat, omit, or reorder.';
  }

  function renderRetainedReplay() {
    const take = retainedReplayImport?.take;
    const verdict = retainedReplayImport?.receipt?.historical_verdict;
    const origin = take
      ? ({dry_run: 'Local preview', retained_replay: 'Saved result'}[take.origin] || take.origin)
      : '';
    $('m1-replay-lineage').textContent = take ? [
      `Origin ${origin}`,
      `Review ${take.qualified ? 'ready' : 'needed'}`,
      `Scene version ${take.scene_revision_id}`,
      `Shot ${take.shot_id}`,
      `Saved output SHA-256 ${take.output.sha256}`,
      `Recorded review ${verdict === 'keeper' ? 'accepted' : verdict ?? 'not present'}`,
    ].join(' · ') : '';
  }
  function retainedReplaySelectionChanged() {
    retainedReplayImport = null;
    renderRetainedReplay();
    const complete = $('m1-replay-file').files.length && $('m1-replay-receipt').files.length;
    $('m1-replay-status').textContent = complete
      ? 'Both saved files selected. Import validates the receipt and exact result before creating one result.'
      : 'Select one saved result file and its matching JSON receipt.';
    setBusy(false);
  }
  function setExportTakeOptions(shotSelect, takeSelect, preserveSelection = false) {
    const selected = preserveSelection ? takeSelect.value : '';
    const candidates = exportTakes[shotSelect.value] || [];
    takeSelect.replaceChildren(new Option('Explicit source', ''));
    candidates.forEach((take) => takeSelect.append(new Option(take.id, take.id)));
    takeSelect.value = selected && candidates.some((take) => take.id === selected)
      ? selected : '';
  }

  function exportControl(row, field) {
    return row.querySelector(`[data-export-field="${field}"]`);
  }

  function exportRow(shot = null, start = 0, end = 0) {
    const row = document.createElement('div');
    row.className = 'm1-export-row';
    row.dataset.exportRow = 'item';
    row.setAttribute('role', 'group');
    row.setAttribute('aria-label', 'Export edit item');
    const shotSelect = document.createElement('select');
    const takeSelect = document.createElement('select');
    const sourceStart = document.createElement('input');
    const sourceEnd = document.createElement('input');
    const keepStart = document.createElement('input');
    const keepEnd = document.createElement('input');
    const up = element('button', {type: 'button', textContent: 'Earlier'});
    const down = element('button', {type: 'button', textContent: 'Later'});
    const remove = element('button', {type: 'button', textContent: 'Remove'});
    shotSelect.dataset.exportField = 'shot';
    takeSelect.dataset.exportField = 'take';
    sourceStart.dataset.exportField = 'source-start';
    sourceEnd.dataset.exportField = 'source-end';
    keepStart.dataset.exportField = 'keep-start';
    keepEnd.dataset.exportField = 'keep-end';
    up.dataset.exportAction = 'earlier';
    down.dataset.exportAction = 'later';
    remove.dataset.exportAction = 'remove';
    for (const field of [sourceStart, sourceEnd, keepStart, keepEnd]) {
      field.type = 'number'; field.min = '0'; field.step = '1';
    }
    keepStart.placeholder = 'auto'; keepEnd.placeholder = 'auto';
    const configure = () => {
      const scene = selectedScene();
      const previousShotId = shotSelect.value;
      shotSelect.replaceChildren(...(scene?.shots || []).map((item) => new Option(item.id, item.id)));
      const selected = scene?.shots.find((item) => item.id === (previousShotId || shot?.id))
        || scene?.shots[0] || null;
      shotSelect.value = selected?.id || '';
      sourceStart.value = String(selected?.source_range.start ?? 0);
      sourceEnd.value = String(selected?.source_range.end ?? 0);
      setExportTakeOptions(shotSelect, takeSelect);
    };
    configure();
    shotSelect.addEventListener('change', configure);
    const labeledControl = (label, control) => element(
      'label', {className: 'm1-export-field'}, [document.createTextNode(label), control],
    );
    row.append(
      labeledControl('Shot', shotSelect),
      labeledControl('Output / take', takeSelect),
      labeledControl('Source start frame', sourceStart),
      labeledControl('Source end frame', sourceEnd),
      labeledControl('Decoder keep start frame (empty is automatic window)', keepStart),
      labeledControl('Decoder keep end frame (empty is automatic window)', keepEnd),
      element('div', {className: 'm1-export-actions', role: 'group', 'aria-label': 'Order and remove item'}, [
        up, down, remove,
      ]),
    );
    const move = (offset) => {
      const rows = [...$('m1-export-list').children];
      const index = rows.indexOf(row);
      const target = index + offset;
      if (target >= 0 && target < rows.length) {
        $('m1-export-list').insertBefore(row, offset < 0 ? rows[target] : rows[target].nextSibling);
      }
    };
    up.addEventListener('click', () => move(-1));
    down.addEventListener('click', () => move(1));
    remove.addEventListener('click', () => {
      row.remove();
      if (!$('m1-export-list').children.length) resetExportEditor();
      setBusy(false);
    });
    $('m1-export-list').append(row);
  }

  function renderExport() {
    const scene = selectedScene();
    if (!scene) {
      resetExportEditor();
      return;
    }
    if (!$('m1-export-list').children.length) scene.shots.forEach((shot) => exportRow(shot));
    else [...$('m1-export-list').children].forEach((row) => setExportTakeOptions(
      exportControl(row, 'shot'), exportControl(row, 'take'), true,
    ));
    setBusy(false);
  }

  async function refreshExportTakes() {
    const scene = selectedScene();
    if (!scene) return;
    const version = ++requestEpoch;
    try {
      const loaded = await Promise.all(scene.shots.map(async (shot) => [shot.id, await requestJSON(
        `/api/projects/${encodeURIComponent(scene.project_id)}/scene-revisions/${encodeURIComponent(scene.id)}/takes?shot_id=${encodeURIComponent(shot.id)}`,
      )]));
      if (!isCurrent(version)) return;
      exportTakes = Object.fromEntries(loaded.map(([shotId, payload]) => [shotId, Array.isArray(payload) ? payload : []]));
      renderExport();
    } catch (error) {
      if (isCurrent(version)) $('m1-export-status').textContent = `Export candidates unavailable: ${error.message}`;
    }
  }

  function collectedEditItems() {
    let timeline = 0;
    return [...$('m1-export-list').children].map((row, index) => {
      const shotSelect = exportControl(row, 'shot');
      const takeSelect = exportControl(row, 'take');
      const sourceStart = exportControl(row, 'source-start');
      const sourceEnd = exportControl(row, 'source-end');
      const keepStartField = exportControl(row, 'keep-start');
      const keepEndField = exportControl(row, 'keep-end');
      const shotId = shotSelect.value;
      const start = Number(sourceStart.value);
      const end = Number(sourceEnd.value);
      const keepStartText = keepStartField.value.trim();
      const keepEndText = keepEndField.value.trim();
      for (const value of [start, end]) {
        if (!Number.isSafeInteger(value) || value < 0) throw new Error(`item ${index + 1} bounds must be non-negative integers`);
      }
      const length = end - start;
      if (length <= 0) throw new Error(`item ${index + 1} must have a positive source range`);
      const keepStart = keepStartText === '' ? null : Number(keepStartText);
      const keepEnd = keepEndText === '' ? null : Number(keepEndText);
      if ((keepStart === null) !== (keepEnd === null)
        || (keepStart !== null && (!Number.isSafeInteger(keepStart) || !Number.isSafeInteger(keepEnd) || keepEnd <= keepStart))) {
        throw new Error(`item ${index + 1} decoder keep must be empty or a positive range`);
      }
      const item = {
        shot_id: shotId,
        take_id: takeSelect.value || null,
        source_range: {start, end},
        decoder_keep: keepStart === null ? null : {start: keepStart, end: keepEnd},
        timeline_range: {start: timeline, end: timeline + length},
      };
      timeline += length;
      return item;
    });
  }

  function renderResolution() {
    const profileSelect = $('m1-profile');
    const previousProfile = profileSelect.value;
    profileSelect.replaceChildren();
    profiles.forEach((entry) => {
      const label = entry.non_inference
        ? `${entry.pin.recipe_id} · ${entry.pin.version} · non-inference CPU routing`
        : `${entry.pin.recipe_id} · ${entry.pin.version}`;
      profileSelect.append(new Option(label, JSON.stringify(entry)));
    });
    if ([...profileSelect.options].some((option) => option.value === previousProfile)) {
      profileSelect.value = previousProfile;
    }
    const sceneSelect = $('m1-scene-select');
    const previousScene = sceneSelect.value;
    sceneSelect.replaceChildren();
    scenes.filter((scene) => scene.shots.some((shot) => shot.kind === 'render'))
      .forEach((scene) => sceneSelect.append(new Option(`Revision ${scene.revision}`, scene.id)));
    if ([...sceneSelect.options].some((option) => option.value === previousScene)) {
      sceneSelect.value = previousScene;
    }
    const scene = selectedScene();
    const shotSelect = $('m1-shot-select');
    const previousShot = shotSelect.value;
    shotSelect.replaceChildren();
    (scene?.shots || []).filter((shot) => shot.kind === 'render')
      .forEach((shot) => shotSelect.append(new Option(shot.id, shot.id)));
    if ([...shotSelect.options].some((option) => option.value === previousShot)) {
      shotSelect.value = previousShot;
    }
    const output = $('m1-resolve-output');
    output.replaceChildren();
    if (!resolvedOperation) {
      output.append(element('div', {}, [element('dt', {}, [document.createTextNode('Settings')]),
        element('dd', {}, [document.createTextNode('Not reviewed')])]));
      return;
    }
    const manifest = JSON.parse(resolvedOperation.canonical_json);
    const referenceHashes = manifest.character.reference_hashes.join(' + ');
    for (const [label, value, compactValue] of [
      ['Fingerprint', resolvedOperation.fingerprint, summaryValue(resolvedOperation.fingerprint)],
      ['Workflow', manifest.graph.resolved_semantic_sha256, summaryValue(manifest.graph.resolved_semantic_sha256)],
      ['References', referenceHashes, `${manifest.character.reference_hashes.length} saved references`],
      ['Audio', manifest.audio_policy],
    ]) {
      const detail = element('dd', {title: value}, [document.createTextNode(compactValue ?? value)]);
      detail.style.overflowWrap = 'anywhere';
      detail.style.wordBreak = 'break-word';
      output.append(element('div', {}, [element('dt', {}, [document.createTextNode(label)]), detail]));
    }
    renderProduction();
  }
  function collectedShots() {
    return [...$('m1-shot-list').children].map((row, index) => {
      const start = Number(row.children[1].value);
      const end = Number(row.children[2].value);
      if (!Number.isInteger(start) || !Number.isInteger(end)) {
        throw new Error(`shot ${index + 1} bounds must be whole integers`);
      }
      return {
        id: row.children[0].value.trim() || `shot-${index + 1}`,
        source_range: {start, end},
        kind: row.children[3].value,
      };
    });
  }
  async function refresh() {
    const version = ++requestEpoch;
    const projectId = window.ProjectsUI?.getState?.().projectId || '';
    setBusy(true);
    if (!projectId) {
      clearSceneSetup('Create or select a saved project before uploading a source.');
      return;
    }
    try {
      const [scenePayload, recipePayload] = await Promise.all([
        requestJSON(`/api/projects/${encodeURIComponent(projectId)}/scenes`),
        requestJSON(`/api/projects/${encodeURIComponent(projectId)}/recipes`),
      ]);
      if (!isCurrent(version)) return;
      scenes = Array.isArray(scenePayload) ? scenePayload : [];
      profiles = Array.isArray(recipePayload.profiles) ? recipePayload.profiles : [];
      renderScenes();
      renderResolution();
      await refreshTakes();
      renderExport();
      await refreshExportTakes();
      $('m1-source-note').textContent = sourceTiming
        ? 'Source inspected. Confirm a complete cut partition when ready.'
        : 'Select a CFR source video to inspect exact decoded timing.';
    } catch (error) {
      if (!isCurrent(version)) return;
      scenes = [];
      profiles = [];
      renderScenes();
      renderResolution();
      renderReview();
      $('m1-source-note').textContent = `Scene revisions unavailable: ${error.message}`;
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  }
  buildResolutionPanel();
  function clearWordTiming() {
    wordTimingEpoch += 1;
    wordTiming = null;
    wordTimingError = false;
    $('m1-word-timing').value = '';
    $('m1-word-status').textContent = 'No word timing selected.';
  }
  function validateWordTiming(value) {
    const exact = (obj, keys) => obj && typeof obj === 'object' && !Array.isArray(obj)
      && Object.keys(obj).length === keys.length && keys.every((key) => Object.hasOwn(obj, key));
    const source = selectedScene()?.source;
    if (!exact(value, ['source_asset_id', 'source_sha256', 'words'])
        || typeof value.source_asset_id !== 'string'
        || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(value.source_asset_id)
        || typeof value.source_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(value.source_sha256)
        || !source || value.source_asset_id !== source.asset_id || value.source_sha256 !== source.sha256
        || !Array.isArray(value.words) || value.words.length < 1 || value.words.length > 512) {
      throw new Error('Invalid word timing shape or stale source association.');
    }
    let end = 0;
    for (const word of value.words) {
      if (!exact(word, ['start', 'end', 'word']) || typeof word.start !== 'number'
          || typeof word.end !== 'number' || !Number.isFinite(word.start) || !Number.isFinite(word.end)
          || word.start < end || word.end <= word.start
          || word.end > source.frame_count * source.timebase.num / source.timebase.den
          || typeof word.word !== 'string' || !word.word.length || [...word.word].length > 128
          || word.word !== word.word.replace(/^[\p{White_Space}\u001c-\u001f]+|[\p{White_Space}\u001c-\u001f]+$/gu, '')
          || /[\u0000-\u001f\u007f]/u.test(word.word)
          || [...word.word].some((c) => c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff)) {
        throw new Error('Invalid word interval, text, order, or source duration.');
      }
      end = word.end;
    }
    return value;
  }
  $('m1-source').addEventListener('change', () => { clearWordTiming(); setBusy(false); });
  $('m1-word-clear').addEventListener('click', clearWordTiming);
  $('m1-word-timing').addEventListener('change', async () => {
    const epoch = ++wordTimingEpoch;
    const file = $('m1-word-timing').files[0];
    wordTiming = null;
    wordTimingError = true;
    try {
      if (!file || file.size > 512 * 1024) throw new Error('Select JSON no larger than 512 KiB.');
      const text = await file.text();
      if (epoch !== wordTimingEpoch) return;
      wordTiming = validateWordTiming(JSON.parse(text));
      wordTimingError = false;
      $('m1-word-status').textContent = `Ready: ${wordTiming.words.length} original-source words.`;
    } catch (error) {
      if (epoch === wordTimingEpoch) $('m1-word-status').textContent = `Word timing refused: ${error.message}`;
    }
  });
  $('m1-replay-file').addEventListener('change', retainedReplaySelectionChanged);
  $('m1-replay-receipt').addEventListener('change', retainedReplaySelectionChanged);
  $('m1-replay-import').addEventListener('click', async () => {
    const workspace = window.ProjectsUI?.getState?.() || {};
    const replayFile = $('m1-replay-file').files[0];
    const receiptFile = $('m1-replay-receipt').files[0];
    if (!workspace.projectId || !replayFile || !receiptFile) return;
    const version = ++requestEpoch;
    setBusy(true);
      $('m1-replay-status').textContent = 'Validating the saved result and receipt…';
    let submitted = false;
    try {
      const receiptText = await receiptFile.text();
      const data = new FormData();
      data.set('file', replayFile);
      data.set('receipt', receiptText);
      submitted = true;
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/replay-import`,
        {method: 'POST', body: data},
      );
      if (!isCurrent(version)) return;
      retainedReplayImport = {take: payload, receipt: JSON.parse(receiptText)};
      takes = [payload, ...takes];
      exportTakes[payload.shot_id] = [payload, ...(exportTakes[payload.shot_id] || [])];
      renderReview();
      renderExport();
      renderRetainedReplay();
      $('m1-replay-status').textContent = `Saved result imported. This is offline retained proof, not fresh provider execution.`;
    } catch (error) {
      if (!isCurrent(version)) return;
      if (!submitted) {
        retainedReplayImport = null;
        renderRetainedReplay();
        $('m1-replay-status').textContent = `Import not submitted: unable to read the receipt locally (${error.message}). The selected result remains selected.`;
      } else if (error?.[responseFacts]?.status === 422 && error[responseFacts].decoded) {
        retainedReplayImport = null;
        renderRetainedReplay();
        $('m1-replay-status').textContent = `Import refused: ${error.message}. No result, review, selection, or export was created.`;
      } else {
        retainedReplayImport = null;
        renderRetainedReplay();
        const facts = error?.[responseFacts];
        const status = typeof facts?.status === 'number' ? ` HTTP ${facts.status}.` : '';
        $('m1-replay-status').textContent = `Import outcome unavailable:${status} The import may already be recorded; inspect current saved state before retrying. No automatic retry was started.`;
      }
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  });
  $('m1-add-shot').addEventListener('click', () => {
    if (!sourceTiming) return;
    const last = $('m1-shot-list').lastElementChild;
    const previousEnd = last ? Number.parseInt(last.children[2].value, 10) : 0;
    shotRow({id: `shot-${$('m1-shot-list').children.length + 1}`, start: previousEnd, end: sourceTiming.frame_count, kind: 'render'});
  });
  $('m1-upload').addEventListener('click', async () => {
    const projectId = window.ProjectsUI?.getState?.().projectId || '';
    const file = $('m1-source').files[0];
    if (!projectId) {
      $('m1-source-note').textContent = 'Create or select a saved project before uploading a source.';
      return;
    }
    if (!file) return;
    const version = ++requestEpoch;
    const data = new FormData();
    data.set('file', file);
    setBusy(true);
    $('m1-source-note').textContent = 'Decoding and hashing the protected source…';
    try {
      const payload = await requestJSON(`/api/projects/${encodeURIComponent(projectId)}/sources`, {method: 'POST', body: data});
      if (!isCurrent(version)) return;
      sourceTiming = payload;
      resetShots(payload.frame_count);
      renderSource();
      $('m1-source-note').textContent = 'Source inspected. Confirm a complete cut partition when ready.';
      $('m1-cut-note').textContent = `Coverage must exactly partition frames 0 through ${payload.frame_count - 1}.`;
    } catch (error) {
      if (!isCurrent(version)) return;
      sourceTiming = null;
      renderSource();
      $('m1-shot-list').replaceChildren();
      $('m1-source-note').textContent = `Source rejected: ${error.message}`;
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  });
  $('m1-confirm').addEventListener('click', async () => {
    if (!sourceTiming) return;
    const projectId = window.ProjectsUI?.getState?.().projectId || '';
    const version = ++requestEpoch;
    setBusy(true);
    $('m1-cut-note').textContent = 'Validating the exact original partition…';
    try {
      const payload = await requestJSON(`/api/projects/${encodeURIComponent(projectId)}/scenes`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({source_asset_id: sourceTiming.asset_id, shots: collectedShots()}),
      });
      if (!isCurrent(version)) return;
      scenes = [payload, ...scenes];
      renderScenes();
      $('m1-cut-note').textContent = `Confirmed fixed scene version ${payload.revision}.`;
    } catch (error) {
      if (!isCurrent(version)) return;
      $('m1-cut-note').textContent = `Could not confirm cuts: ${error.message}`;
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  });
  for (const id of ['m1-profile', 'm1-scene-select']) {
    $(id).addEventListener('change', () => {
      if (id === 'm1-scene-select') clearWordTiming();
      $('m1-shot-select').value = '';
      renderResolution();
      setBusy(false);
      refreshTakes();
      resetExportEditor();
      renderExport();
      refreshExportTakes();
    });
  }
  $('m1-shot-select').addEventListener('change', () => setBusy(false));
  $('m1-review-shot').addEventListener('change', () => {
    selectedTakeId = null;
    challengerIncumbentTakeId = null;
    selectionRevision = 0;
    renderReview();
    refreshTakes();
  });
  $('m1-seed').addEventListener('input', () => setBusy(false));
  $('m1-resolve').addEventListener('click', async () => {
    const workspace = window.ProjectsUI?.getState?.() || {};
    const references = window.ProjectsUI?.getReferenceState?.() || {};
    const seedText = $('m1-seed').value;
    const seed = Number(seedText);
    if (!workspace.projectId || !workspace.characterId || !workspace.characterVersion
        || !references.ready || seedText.trim() === '' || !Number.isSafeInteger(seed) || seed < 0) {
      $('m1-resolve-note').textContent = 'Select this project, one original shot, and one saved performer version.';
      return;
    }
    const version = ++requestEpoch;
    setBusy(true);
    $('m1-resolve-note').textContent = 'Collecting read-only inputs…';
    try {
      if (wordTimingError) throw new Error('Clear or replace the refused word timing file.');
      if (wordTiming) validateWordTiming(wordTiming);
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/operations/resolve`,
        {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            scene_revision_id: $('m1-scene-select').value,
            shot_id: $('m1-shot-select').value,
            pin: JSON.parse($('m1-profile').value).pin,
            character_version: [workspace.characterId, workspace.characterVersion],
            seed,
            rights_attested: $('m1-rights').checked,
            ...(wordTiming ? {word_timing: wordTiming} : {}),
          }),
        },
      );
      if (!isCurrent(version)) return;
      resolvedOperation = payload;
      challengerIncumbentTakeId = challengerAttemptId = challengerRequestKey = null;
      renderResolution();
      renderReview();
      $('m1-resolve-note').textContent = 'Prepared settings resolved. No execution attempt, submission, renderer connection, or spending was created.';
    } catch (error) {
      if (!isCurrent(version)) return;
      resolvedOperation = null;
      renderResolution();
      $('m1-resolve-note').textContent = `Resolution refused: ${error.message}`;
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  });
  async function refreshAttempts() {
    const workspace = window.ProjectsUI?.getState?.() || {};
    if (!workspace.projectId) {
      attempts = [];
      authorizedAttemptId = null;
      renderProduction();
      return;
    }
    const version = ++attemptEpoch;
    try {
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/attempts`,
      );
      if (!isAttemptCurrent(version)) return;
      attempts = Array.isArray(payload) ? payload : [];
      if (!authorizedAttemptId) {
        const candidates = attempts.filter((attempt) => attempt.operation_id === resolvedOperation?.id);
        if (candidates.length === 1) authorizedAttemptId = candidates[0].id;
      }
      renderProduction();
      setBusy(false);
    } catch (error) {
      if (!isAttemptCurrent(version)) return;
      $('m1-production-note').textContent = `Attempt status unavailable: ${error.message}`;
    }
  }
  $('m1-mode').addEventListener('change', () => {
    if ($('m1-mode').value !== 'dry_run') {
      $('m1-production-note').textContent = 'Live rendering requires separate setup and authorization.';
    }
    setBusy(false);
  });
  $('m1-authorize-rights').addEventListener('change', () => setBusy(false));
  $('m1-incumbent-select').addEventListener('change', () => {
    challengerIncumbentTakeId = $('m1-incumbent-select').value || null; renderChallenger(); setBusy(false);
  });
  $('m1-challenger-rights').addEventListener('change', () => setBusy(false));
  $('m1-authorize').addEventListener('click', async () => {
    const workspace = window.ProjectsUI?.getState?.() || {};
    if (!resolvedOperation || !workspace.projectId || $('m1-mode').value !== 'dry_run'
      || !$('m1-authorize-rights').checked) {
      return;
    }
    authorizedRequestKey = `m1-${resolvedOperation.fingerprint}`;
    const version = ++attemptEpoch;
    setBusy(true);
    $('m1-production-note').textContent = 'Recording one explicit preview authorization…';
    try {
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/attempts`,
        {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            operation_id: resolvedOperation.id,
            client_request_id: authorizedRequestKey,
            mode: 'dry_run',
            challenger_of: null,
          }),
        },
      );
      if (!isAttemptCurrent(version)) return;
      authorizedAttemptId = payload.id;
      await refreshAttempts();
      $('m1-production-note').textContent = 'Preview authorization recorded. The background worker owns submission and recovery.';
    } catch (error) {
      if (!isAttemptCurrent(version)) return;
      $('m1-production-note').textContent = `Authorization response unavailable: ${error.message}. Retry uses the same key and cannot enqueue another attempt.`;
    } finally {
      if (isAttemptCurrent(version)) setBusy(false);
    }
  });
  $('m1-challenger-authorize').addEventListener('click', async () => {
    const workspace = window.ProjectsUI?.getState?.() || {};
    const incumbent = selectedIncumbentTake();
    if (!resolvedOperation || !incumbent || !workspace.projectId
      || $('m1-mode').value !== 'dry_run' || !$('m1-challenger-rights').checked) return;
    challengerRequestKey = `m1-challenge-${resolvedOperation.fingerprint}-${incumbent.attempt_id}`;
    const version = ++attemptEpoch;
    setBusy(true);
    $('m1-challenger-note').textContent = 'Recording one alternate preview for this shot…';
    try {
      const payload = await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/attempts`,
        {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            operation_id: resolvedOperation.id,
            client_request_id: challengerRequestKey,
            mode: 'dry_run',
            challenger_of: incumbent.attempt_id,
          }),
        },
      );
      if (!isAttemptCurrent(version)) return;
      challengerAttemptId = payload.id;
      authorizedAttemptId = payload.id;
      await refreshAttempts();
      $('m1-challenger-note').textContent = 'Alternate preview recorded. Retry uses the same request key and cannot enqueue another attempt.';
    } catch (error) {
      if (!isAttemptCurrent(version)) return;
      $('m1-challenger-note').textContent = `Challenger response unavailable: ${error.message}. Retry uses the same key and cannot enqueue another attempt.`;
    } finally {
      if (isAttemptCurrent(version)) setBusy(false);
    }
  });
  $('m1-cancel').addEventListener('click', async () => {
    const workspace = window.ProjectsUI?.getState?.() || {};
    const attempt = currentAttempt();
    if (!workspace.projectId || !attempt) return;
    const version = ++attemptEpoch;
    setBusy(true);
    $('m1-production-note').textContent = 'Recording durable cancellation intent…';
    try {
      await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/attempts/${encodeURIComponent(attempt.id)}/cancel`,
        {method: 'POST'},
      );
      if (!isAttemptCurrent(version)) return;
      await refreshAttempts();
      $('m1-production-note').textContent = 'Cancellation state is shown from the durable attempt record; no refund is claimed.';
    } catch (error) {
      if (!isAttemptCurrent(version)) return;
      $('m1-production-note').textContent = `Cancellation request failed: ${error.message}`;
    } finally {
      if (isAttemptCurrent(version)) setBusy(false);
    }
  });
  $('m1-reconcile').addEventListener('click', async () => {
    const workspace = window.ProjectsUI?.getState?.() || {};
    const attempt = currentAttempt();
    if (!workspace.projectId || !attempt) return;
    const version = ++attemptEpoch;
    setBusy(true);
    try {
      await requestJSON(
        `/api/projects/${encodeURIComponent(workspace.projectId)}/attempts/${encodeURIComponent(attempt.id)}/reconcile`,
        {method: 'POST'},
      );
      if (!isAttemptCurrent(version)) return;
      await refreshAttempts();
      $('m1-production-note').textContent = 'Reconciliation requested for the existing receipt only. Unknown outcomes stay pending; this does not authorize another attempt.';
    } catch (error) {
      if (isAttemptCurrent(version)) $('m1-production-note').textContent = `Reconciliation request failed: ${error.message}`;
    } finally {
      if (isAttemptCurrent(version)) setBusy(false);
    }
  });
  $('m1-review-append').addEventListener('click', async () => {
    const take = takes.find((item) => item.id === selectedTakeId);
    const note = $('m1-review-note').value.trim();
    if (!take || !note) {
      $('m1-review-note-status').textContent = 'Compare and select one candidate, then provide a human review note.';
      return;
    }
    let collab = null;
    try { collab = JSON.parse(localStorage.getItem('recastroom-collab-v1') || 'null'); } catch (_) { collab = null; }
    const attributedNote = collab?.mode === 'handoff' && collab.reviewer
      ? `${collab.reviewer}: ${note}`.slice(0, 4000) : note;
    try {
      const payload = await requestJSON('/takes/' + encodeURIComponent(take.id) + '/reviews', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({verdict: $('m1-review-verdict').value, note: attributedNote}),
      });
      const verdictLabel = {keeper: 'accepted', needs_review: 'needs review', reject: 'rejected'}[payload.verdict] || payload.verdict;
      $('m1-review-note-status').textContent = `Human review ${verdictLabel} and appended as ${payload.id}; no automatic selection was made.`;
    } catch (error) {
      $('m1-review-note-status').textContent = `Review append failed: ${error.message}`;
    }
  });
  $('m1-deselect').addEventListener('click', () => selectCandidate(null));
  $('m1-selection-refresh').addEventListener('click', () => {
    selectionRevision = 0;
      $('m1-review-note-status').textContent = 'Selection state refreshed; server history is unchanged.';
  });
  $('m1-export-add').addEventListener('click', () => {
    const scene = selectedScene();
    const shot = scene?.shots[0];
    if (scene && shot) exportRow(shot);
    setBusy(false);
  });
  $('m1-create-edit').addEventListener('click', async () => {
    const scene = selectedScene();
    const workspace = window.ProjectsUI?.getState?.() || {};
    if (!scene || workspace.projectId !== scene.project_id) return;
    const version = ++requestEpoch;
    setBusy(true);
    $('m1-export-status').textContent = 'Saving the explicit edit list…';
    try {
      const items = collectedEditItems();
      const payload = await requestJSON(`/api/projects/${encodeURIComponent(scene.project_id)}/edit-revisions`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          scene_revision_id: scene.id,
          items,
          audio: $('m1-audio-policy').value,
          timebase: scene.source.timebase,
        }),
      });
      if (!isCurrent(version)) return;
      editRevision = payload;
      exportRecord = null;
      $('m1-export-download').hidden = true;
      $('m1-export-status').textContent = `Fixed edit version ${payload.id}; later selections cannot change it.`;
    } catch (error) {
      if (!isCurrent(version)) return;
      editRevision = null;
      $('m1-export-status').textContent = `Edit refused: ${error.message}`;
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  });
  $('m1-export').addEventListener('click', async () => {
    if (!editRevision) return;
    const version = ++requestEpoch;
    setBusy(true);
      $('m1-export-status').textContent = 'Assembling and checking the protected export…';
    try {
      const payload = await requestJSON(`/edit-revisions/${encodeURIComponent(editRevision.id)}/exports`, {method: 'POST'});
      if (!isCurrent(version)) return;
      exportRecord = payload;
      const download = $('m1-export-download');
      download.href = `/exports/${encodeURIComponent(payload.id)}/artifact`;
      download.hidden = false;
      download.textContent = `Download result`;
      $('m1-export-status').textContent = `Export completed with SHA-256 ${payload.sha256}.`;
    } catch (error) {
      if (isCurrent(version)) $('m1-export-status').textContent = `Export refused: ${error.message}`;
    } finally {
      if (isCurrent(version)) setBusy(false);
    }
  });
  document.addEventListener('projects:selection-change', () => {
    clearSceneSetup('Project changed. Upload and inspect a source for the selected project.');
    refresh();
  });
  document.addEventListener('projects:prepared', () => refresh());
  document.addEventListener('studio:reset', () => {
    clearSceneSetup('Local source selection cleared. Saved scene revisions remain unchanged.');
    refresh();
  });
  setInterval(refreshAttempts, 1000);
  window.M1UI = Object.freeze({refresh, getState: () => ({
    requestEpoch,
    sourceTiming,
    wordTiming,
    scenes,
    profiles,
    resolvedOperation,
    attempts,
    authorizedAttemptId,
    authorizedRequestKey,
    challengerIncumbentTakeId,
    challengerAttemptId,
    challengerRequestKey,
    retainedReplayImport,
    takes,
    selectedTakeId,
    selectionRevision,
    exportTakes,
    editRevision,
    exportRecord,
  })});
  clearSceneSetup();
  refresh();
})();

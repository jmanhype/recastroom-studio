/* SPDX-License-Identifier: MIT */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const projectsKey = 'recastroom.projectId';
  const characterKey = (projectId) => `recastroom.characterVersion.${projectId}`;
  let requestEpoch = 0;
  let projects = [];
  let characters = [];
  let selectedProjectId = '';
  let selectedCharacterId = '';
  let selectedCharacterVersion = 0;
  let selectedReferences = [];
  let workspaceBusy = false;
  const isCurrent = (version) => version === requestEpoch;
  const message = (value, fallback) => {
    if (typeof value === 'string') return value;
    if (Array.isArray(value)) return value.map((item) => item?.msg || 'Invalid input').join('; ');
    if (value && typeof value === 'object') return String(value.message || value.msg || fallback);
    return fallback;
  };
  class APIError extends Error {}
  async function requestJSON(path, options = {}) {
    let response;
    let payload = null;
    try {
      response = await fetch(path, options);
      payload = await response.json();
    } catch (_) {
      throw new APIError('Server response unavailable. Check the connection and retry.');
    }
    if (!response.ok) {
      throw new APIError(message(payload?.detail, `Request failed (${response.status}).`));
    }
    return payload;
  }
  function setBusy(next) {
    workspaceBusy = next;
    $('create-project').disabled = workspaceBusy || !$('project-name').value.trim();
    $('create-character').disabled = workspaceBusy
      || !$('project-select').value
      || !$('character-name').value.trim()
      || !$('character-reference-1').files.length;
  }
  function syncHiddenFields() {
    $('project-id-input').value = selectedProjectId;
    $('character-id-input').value = selectedCharacterId;
    $('character-version-input').value = selectedCharacterId ? String(selectedCharacterVersion) : '';
    $('reference_1').required = !selectedCharacterId;
  }
  function dispatchSelection() {
    document.dispatchEvent(new CustomEvent('projects:selection-change', {
      detail: {
        projectId: selectedProjectId,
        characterId: selectedCharacterId,
        characterVersion: selectedCharacterVersion,
        savedReferenceReady: Boolean(selectedCharacterId && selectedReferences.length),
      },
    }));
  }
  function clearReferenceUploads() {
    $('reference_1').value = '';
    $('reference_2').value = '';
  }
  function renderReferences() {
    const container = $('character-references');
    container.replaceChildren();
    selectedReferences.forEach((asset) => {
      const figure = document.createElement('figure');
      const image = document.createElement('img');
      if (/^[0-9a-f]{32}$/.test(asset.asset_id || '')) image.src = `/api/assets/${asset.asset_id}`;
      image.alt = `Saved reference: ${asset.filename || 'protected asset'}`;
      const caption = document.createElement('figcaption');
      caption.textContent = `${asset.filename || 'Reference'} · ${asset.protected ? 'protected' : 'unprotected'}`;
      figure.append(image, caption);
      container.append(figure);
    });
  }
  function renderCharacters() {
    const selected = characters.find((item) => item.character.character_id === selectedCharacterId
      && item.character.version === selectedCharacterVersion);
    const select = $('character-select');
    select.replaceChildren(new Option('Upload references for this job', ''));
    characters.forEach((item) => {
      const value = `${item.character.character_id}:${item.character.version}`;
      select.append(new Option(`${item.character.name} · v${item.character.version}`, value));
    });
    if (selected) {
      select.value = `${selected.character.character_id}:${selected.character.version}`;
      selectedReferences = selected.references;
    } else {
      select.value = '';
      selectedCharacterId = '';
      selectedCharacterVersion = 0;
      selectedReferences = [];
    }
    renderReferences();
    syncHiddenFields();
    dispatchSelection();
  }
  function renderProjects() {
    const select = $('project-select');
    select.replaceChildren(new Option('Upload-only · no saved history', ''));
    projects.forEach((project) => select.append(new Option(project.name, project.project_id)));
    select.value = selectedProjectId && projects.some((item) => item.project_id === selectedProjectId)
      ? selectedProjectId
      : '';
    if (!select.value) selectedProjectId = '';
  }
  function selectCharacter(item, {persist = true, notify = true} = {}) {
    selectedCharacterId = item?.character.character_id || '';
    selectedCharacterVersion = item?.character.version || 0;
    selectedReferences = item?.references || [];
    if (selectedProjectId && persist) {
      localStorage.setItem(characterKey(selectedProjectId), `${selectedCharacterId}:${selectedCharacterVersion}`);
    }
    if (selectedCharacterId) clearReferenceUploads();
    renderCharacters();
    if (notify) dispatchSelection();
  }
  function clearHistory(messageText = 'No prepared configuration links yet.') {
    $('project-history').replaceChildren();
    const empty = document.createElement('li');
    empty.textContent = messageText;
    $('project-history').append(empty);
  }
  function renderHistory(jobs) {
    const history = $('project-history');
    history.replaceChildren();
    if (!jobs.length) {
      const empty = document.createElement('li');
      empty.textContent = 'No prepared configuration links yet.';
      history.append(empty);
      return;
    }
    jobs.forEach((job) => {
      const row = document.createElement('li');
      const heading = document.createElement('strong');
      heading.textContent = `JOB / ${job.job_id}`;
      const details = document.createElement('small');
      details.textContent = `seed ${job.seed} · references ${job.config?.reference_names?.join(' + ') || 'n/a'} · ${job.character_id ? `character v${job.character_version}` : 'uploaded references'}`;
      const links = document.createElement('span');
      for (const [href, label] of [
        [job.workflow_url, 'Workflow JSON'],
        [job.prompt_url, 'Prompt'],
      ]) {
        const link = document.createElement('a');
        link.href = href;
        link.textContent = label;
        links.append(link);
      }
      row.append(heading, details, links);
      history.append(row);
    });
  }
  async function loadHistory(projectId, version) {
    if (!isCurrent(version)) return;
    if (!projectId) {
      clearHistory('Upload-only mode keeps the existing no-project behavior.');
      return;
    }
    try {
      const payload = await requestJSON(`/api/projects/${encodeURIComponent(projectId)}/jobs`);
      if (!isCurrent(version)) return;
      renderHistory(payload.jobs || []);
      $('project-note').textContent = 'Saved project and server-backed history restored.';
    } catch (error) {
      if (!isCurrent(version)) return;
      clearHistory();
      $('project-note').textContent = `Project history unavailable: ${error.message}`;
    }
  }
  async function selectProject(projectId, version = ++requestEpoch, {restoreCharacter = false} = {}) {
    selectedProjectId = projectId;
    localStorage.setItem(projectsKey, projectId);
    selectedCharacterId = '';
    selectedCharacterVersion = 0;
    selectedReferences = [];
    renderProjects();
    if (restoreCharacter && projectId) {
      const saved = localStorage.getItem(characterKey(projectId)) || '';
      const [characterId, versionText] = saved.split(':');
      const parsedVersion = Number.parseInt(versionText, 10);
      const item = characters.find((entry) => entry.character.character_id === characterId
        && entry.character.version === parsedVersion);
      if (item) {
        selectedCharacterId = item.character.character_id;
        selectedCharacterVersion = item.character.version;
        selectedReferences = item.references;
      }
    }
    renderCharacters();
    dispatchSelection();
    await loadHistory(projectId, version);
    if (!projectId) $('project-note').textContent = 'Upload-only mode is active. Create or select a project to save reusable references.';
    setBusy(false);
  }
  async function initialize() {
    const version = ++requestEpoch;
    setBusy(true);
    $('project-note').textContent = 'Loading saved projects…';
    try {
      const [projectPayload, characterPayload] = await Promise.all([
        requestJSON('/api/projects'),
        requestJSON('/api/characters'),
      ]);
      if (!isCurrent(version)) return;
      projects = projectPayload.projects || [];
      characters = characterPayload.characters || [];
      const savedProject = localStorage.getItem(projectsKey) || '';
      await selectProject(
        projects.some((item) => item.project_id === savedProject) ? savedProject : '',
        version,
        {restoreCharacter: true},
      );
    } catch (error) {
      if (!isCurrent(version)) return;
      $('project-note').textContent = `Saved projects unavailable: ${error.message}`;
      $('character-note').textContent = 'Character library unavailable. Upload-only mode remains usable.';
      clearHistory('Saved history is unavailable in upload-only mode.');
      setBusy(false);
    }
  }
  $('project-select').addEventListener('change', () => {
    selectProject($('project-select').value);
  });
  $('character-select').addEventListener('change', () => {
    const [characterId, versionText] = $('character-select').value.split(':');
    const version = Number.parseInt(versionText, 10);
    selectCharacter(characters.find((item) => item.character.character_id === characterId
      && item.character.version === version));
  });
  for (const id of ['project-name', 'character-name']) {
    $(id).addEventListener('input', () => setBusy(workspaceBusy));
    $(id).addEventListener('change', () => setBusy(workspaceBusy));
    $(id).addEventListener('keyup', () => setBusy(workspaceBusy));
  }
  $('character-reference-1').addEventListener('change', () => setBusy(workspaceBusy));
  $('create-project').addEventListener('click', async () => {
    if ($('create-project').disabled) return;
    const version = ++requestEpoch;
    const name = $('project-name').value.trim();
    setBusy(true);
    $('project-note').textContent = 'Creating project…';
    try {
      const project = await requestJSON('/api/projects', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name}),
      });
      if (!isCurrent(version)) return;
      projects = [...projects, project].sort((a, b) => a.name.localeCompare(b.name));
      $('project-name').value = '';
      await selectProject(project.project_id, version);
    } catch (error) {
      if (!isCurrent(version)) return;
      $('project-note').textContent = `Could not create project: ${error.message}`;
      setBusy(false);
    }
  });
  $('create-character').addEventListener('click', async () => {
    if ($('create-character').disabled) return;
    const version = ++requestEpoch;
    const projectId = selectedProjectId;
    const data = new FormData();
    data.set('project_id', projectId);
    data.set('name', $('character-name').value.trim());
    data.set('description', $('character-description').value);
    data.set('reference_1', $('character-reference-1').files[0]);
    if ($('character-reference-2').files[0]) data.set('reference_2', $('character-reference-2').files[0]);
    setBusy(true);
    $('character-note').textContent = 'Saving immutable character version…';
    try {
      const created = await requestJSON('/api/characters', {method: 'POST', body: data});
      if (!isCurrent(version)) return;
      characters = [...characters, created];
      $('character-name').value = '';
      $('character-description').value = '';
      $('character-reference-1').value = '';
      $('character-reference-2').value = '';
      selectCharacter(created, {persist: true, notify: false});
      $('character-note').textContent = `Saved ${created.character.name} version ${created.character.version}. It is ready for reuse.`;
      setBusy(false);
    } catch (error) {
      if (!isCurrent(version)) return;
      $('character-note').textContent = `Could not save character: ${error.message}`;
      setBusy(false);
    }
  });
  for (const id of ['reference_1', 'reference_2']) {
    $(id).addEventListener('change', () => {
      if (!selectedCharacterId) return;
      $('character-select').value = '';
      localStorage.removeItem(characterKey(selectedProjectId));
      selectCharacter(null, {persist: false});
      $('character-note').textContent = 'Uploaded references selected. The saved character version was cleared for this job.';
    });
  }
  document.addEventListener('projects:prepared', (event) => {
    const projectId = event.detail?.project_id;
    if (projectId && projectId === selectedProjectId) loadHistory(projectId, ++requestEpoch);
  });
  document.addEventListener('studio:reset', () => {
    if (selectedCharacterId) selectCharacter(null, {persist: false});
    syncHiddenFields();
    $('character-note').textContent = 'Character selection cleared. Saved versions and history remain unchanged.';
  });
  window.ProjectsUI = Object.freeze({
    getState: () => ({
      projectId: selectedProjectId,
      characterId: selectedCharacterId,
      characterVersion: selectedCharacterVersion,
      requestEpoch,
    }),
    getReferenceState: () => ({
      ready: Boolean(selectedCharacterId && selectedReferences.length),
      references: [...selectedReferences],
    }),
    refresh: initialize,
  });
  setBusy(false);
  initialize();
})();

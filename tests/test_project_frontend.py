# SPDX-License-Identifier: MIT
"""Server-backed frontend contract regressions for connected projects."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

from fastapi.testclient import TestClient

from openjutsu.config import load_settings


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/synthetic_source.mp4"
REFERENCE = ROOT / "tests/fixtures/synthetic_reference.png"
NODE = Path("/opt/homebrew/opt/node@22/bin/node")


def run_real_projects_reset(mode: str) -> dict:
    harness = r'''
const fs = require('fs');
const vm = require('vm');
const mode = process.argv[2];
const projectId = mode === 'no-project' ? '' : 'a'.repeat(32);
const characterId = 'char_' + 'b'.repeat(24);
const requests = [];
class FakeCustomEvent { constructor(type, options = {}) { this.type = type; this.detail = options.detail; } }
class FakeOption { constructor(text, value) { this.text = text; this.value = value; } }
function element(id, name = '') {
  return {id, name, value: '', disabled: false, required: false, files: [], textContent: '',
    children: [], listeners: {}, append(...nodes) { this.children.push(...nodes); },
    replaceChildren(...nodes) { this.children = nodes; },
    addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); },
    dispatchEvent(event) { (this.listeners[event.type] || []).forEach((handler) => handler(event)); }};
}
const ids = ['project-select', 'project-name', 'create-project', 'project-note', 'character-select',
  'character-references', 'character-name', 'character-reference-1', 'character-reference-2',
  'character-description', 'create-character', 'character-note', 'project-history',
  'project-id-input', 'character-id-input', 'character-version-input', 'reference_1', 'reference_2'];
const names = { 'project-id-input': 'project_id', 'character-id-input': 'character_id',
  'character-version-input': 'character_version', 'reference_1': 'reference_1', 'reference_2': 'reference_2' };
const byId = Object.fromEntries(ids.map((id) => [id, element(id, names[id] || '')]));
const formControls = ['project-id-input', 'character-id-input', 'character-version-input',
  'reference_1', 'reference_2'].map((id) => byId[id]);
const document = {
  getElementById: (id) => byId[id], listeners: {},
  createElement: () => element('generated'),
  dispatchEvent(event) { (this.listeners[event.type] || []).forEach((handler) => handler(event)); },
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); },
};
const savedCharacter = mode === 'saved-character';
const storage = new Map([['recastroom.projectId', projectId]]);
if (savedCharacter) storage.set(`recastroom.characterVersion.${projectId}`, `${characterId}:1`);
const projects = projectId ? [{project_id: projectId, name: 'Project A'}] : [];
const characters = savedCharacter ? [{character: {character_id: characterId, version: 1},
  references: [{asset_id: 'c'.repeat(32), filename: 'saved.png', protected: true}]}] : [];
async function fetch(path) {
  requests.push(path);
  const payload = path === '/api/projects' ? {projects}
    : path === '/api/characters' ? {characters}
    : path === `/api/projects/${projectId}/jobs` ? {projectId, jobs: []}
    : {error: `unexpected endpoint ${path}`};
  return {ok: path !== '/unexpected', json: async () => payload};
}
const context = {console, document, fetch, Option: FakeOption, CustomEvent: FakeCustomEvent,
  FormData, File, localStorage: {
    getItem: (key) => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: (key) => storage.delete(key),
  }};
context.window = context;
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), vm.createContext(context),
  {filename: process.argv[1]});
async function settle() { for (let index = 0; index < 12; index += 1) await Promise.resolve(); }
function snapshot() {
  return {projectSelect: byId['project-select'].value,
    projectsState: context.ProjectsUI.getState(), hiddenProject: byId['project-id-input'].value,
    hiddenCharacter: byId['character-id-input'].value,
    hiddenVersion: byId['character-version-input'].value,
    characterSelect: byId['character-select'].value,
    referenceRequired: byId['reference_1'].required,
    referenceState: context.ProjectsUI.getReferenceState()};
}
function resetForm() {
  byId['project-id-input'].value = '';
  byId['character-id-input'].value = '';
  byId['character-version-input'].value = '';
  byId['reference_1'].value = '';
  byId['reference_2'].value = '';
}
(async () => {
  await settle();
  const before = snapshot();
  resetForm();
  document.dispatchEvent(new FakeCustomEvent('studio:reset'));
  await settle();
  const data = new FormData();
  for (const control of formControls) if (control.name && control.value !== '') data.set(control.name, control.value);
  data.set('source', new File(['source'], 'source.mp4', {type: 'video/mp4'}));
  data.set('reference_1', new File(['reference'], 'uploaded.png', {type: 'image/png'}));
  console.log(JSON.stringify({mode, before, after: snapshot(), requests,
    formData: {project_id: data.get('project_id') || '', character_id: data.get('character_id') || '',
      character_version: data.get('character_version') || '',
      source: data.get('source') instanceof File, reference_1: data.get('reference_1') instanceof File}}));
})().catch((error) => { console.error(error.stack); process.exit(1); });
'''
    completed = subprocess.run(
        [str(NODE), "-e", harness, str(ROOT / "app/web/projects.js"), mode],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def studio(tmp_path: Path):
    import app.main as main

    original_settings = main.SETTINGS
    original_store = main.PROJECT_STORE
    original_status = main.JOB_STATUS.copy()
    original_locks = main.JOB_LOCKS.copy()
    main.SETTINGS = load_settings(
        {"OPENJUTSU_BACKEND": "dry_run", "OPENJUTSU_DATA_DIR": str(tmp_path)}
    )
    try:
        with TestClient(main.app) as client:
            client.get("/api/health")
            yield main, client
    finally:
        main.SETTINGS = original_settings
        main.PROJECT_STORE = original_store
        main.app.state.workspace_store = original_store
        main.JOB_STATUS.clear(); main.JOB_STATUS.update(original_status)
        main.JOB_LOCKS.clear(); main.JOB_LOCKS.update(original_locks)


def test_project_controls_are_keyboard_accessible_and_safe_by_default(tmp_path):
    for _ in (None,):
        generator = studio(tmp_path)
        _main, client = next(generator)
        try:
            home = client.get("/")
            projects = client.get("/projects.js")
            studio_js = client.get("/studio.js")
            stylesheet = client.get("/styles.css")
            assert all(
                response.status_code == 200
                for response in (home, projects, studio_js, stylesheet)
            )
            html = home.text
            for element_id in (
                "projects-heading", "project-select", "project-name", "create-project",
                "character-select", "character-reference-1", "character-reference-2",
                "character-references", "project-history",
            ):
                assert f'id="{element_id}"' in html
            assert 'name="project_id"' in html
            assert 'name="character_id"' in html
            assert 'name="character_version"' in html
            assert html.index('/projects.js') < html.index('/studio.js')
            assert "Selecting or reloading never starts a run" in html

            project_js = projects.text
            assert "let requestEpoch = 0" in project_js
            assert "const isCurrent = (version) => version === requestEpoch" in project_js
            assert "if (!isCurrent(version)) return" in project_js
            assert "/api/assets/" in project_js
            assert "localStorage" in project_js
            assert "projects:prepared" in project_js
            assert "projects:selection-change" in project_js
            assert "studio:reset" in project_js
            assert "$('reference_1').required = !selectedCharacterId" in project_js
            assert "URL.createObjectURL" not in project_js
            assert "/run" not in project_js
            assert "window.StudioUI" not in project_js

            ui = studio_js.text
            assert "window.ProjectsUI?.getReferenceState" in ui
            assert "savedReferences?.ready" in ui
            assert "if (value === '' || (value instanceof File && !value.name)) data.delete(name)" in ui
            assert "document.dispatchEvent(new CustomEvent('projects:prepared'" in ui
            assert "document.dispatchEvent(new CustomEvent('studio:reset')" in ui

            css = stylesheet.text
            assert ".projects-grid select:focus-visible" in css
            assert "@media(prefers-reduced-motion:reduce)" in css
            assert "animation:none!important" in css
            assert "transition:none!important" in css
            assert not re.search(r"(?i)percent complete|quality score|automatically run", html + project_js)
        finally:
            generator.close()


def test_project_history_and_safe_asset_previews_are_browser_consumable(tmp_path):
    generator = studio(tmp_path)
    _main, client = next(generator)
    try:
        project = client.post("/api/projects", json={"name": "Browser fixture"}).json()
        character = client.post(
            "/api/characters",
            data={"project_id": project["project_id"], "name": "Fixture Performer"},
            files={"reference_1": ("browser.png", REFERENCE.read_bytes(), "image/png")},
        ).json()
        prepared = client.post(
            "/api/prepare",
            files={"source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4")},
            data={
                "rights_attested": "true",
                "seed": "81",
                "project_id": project["project_id"],
                "character_id": character["character"]["character_id"],
                "character_version": "1",
            },
        )
        assert prepared.status_code == 200, prepared.text
        history = client.get(f"/api/projects/{project['project_id']}/jobs").json()
        assert len(history["jobs"]) == 1
        asset_id = character["references"][0]["asset_id"]
        assert re.fullmatch(r"[0-9a-f]{32}", asset_id)
        preview = client.get(f"/api/assets/{asset_id}")
        assert preview.status_code == 200
        assert preview.headers["content-type"] == "image/png"
        assert preview.content == REFERENCE.read_bytes()
        safe_payloads = prepared.text + str(history) + str(character)
        assert str(tmp_path) not in safe_payloads
        assert "/Users/" not in safe_payloads
        assert "blob:" not in client.get("/projects.js").text
    finally:
        generator.close()


def test_real_projects_reset_synchronizes_hidden_project_state(tmp_path):
    project_id = "a" * 32
    character_id = "char_" + "b" * 24
    for mode in ("no-character", "saved-character", "no-project"):
        result = run_real_projects_reset(mode)
        before = result["before"]
        after = result["after"]
        expected_project = "" if mode == "no-project" else project_id
        expected_character = character_id if mode == "saved-character" else ""
        assert before["projectSelect"] == expected_project
        assert before["hiddenProject"] == expected_project
        assert before["hiddenCharacter"] == expected_character
        assert after["projectSelect"] == expected_project
        assert after["projectsState"]["projectId"] == expected_project
        assert after["hiddenProject"] == expected_project
        assert after["hiddenCharacter"] == ""
        assert after["hiddenVersion"] == ""
        assert after["characterSelect"] == ""
        assert after["referenceRequired"] is True
        assert after["referenceState"] == {"ready": False, "references": []}
        assert result["formData"] == {
            "project_id": expected_project,
            "character_id": "",
            "character_version": "",
            "source": True,
            "reference_1": True,
        }
        assert all("/run" not in path for path in result["requests"])


def test_real_store_and_api_records_survive_frontend_reset(tmp_path):
    generator = studio(tmp_path)
    _main, client = next(generator)
    try:
        project = client.post("/api/projects", json={"name": "Reset fixture"}).json()
        character = client.post(
            "/api/characters",
            data={"project_id": project["project_id"], "name": "Immutable Performer"},
            files={"reference_1": ("protected.png", REFERENCE.read_bytes(), "image/png")},
        ).json()
        prepared = client.post(
            "/api/prepare",
            files={
                "source": (SOURCE.name, SOURCE.read_bytes(), "video/mp4"),
                "reference_1": ("uploaded.png", REFERENCE.read_bytes(), "image/png"),
            },
            data={"rights_attested": "true", "project_id": project["project_id"]},
        )
        assert prepared.status_code == 200, prepared.text
        job_id = prepared.json()["job_id"]

        def snapshot():
            job_dir = _main.SETTINGS.data_dir / "jobs" / job_id
            return {
                "project": client.get(f"/api/projects/{project['project_id']}").json(),
                "character": client.get(
                    f"/api/characters/{character['character']['character_id']}/versions/1"
                ).json(),
                "history": client.get(
                    f"/api/projects/{project['project_id']}/jobs"
                ).json(),
                "protected_bytes": client.get(
                    f"/api/assets/{character['references'][0]['asset_id']}"
                ).content,
                "artifacts": {
                    str(path.relative_to(job_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(job_dir.rglob("*"))
                    if path.is_file()
                },
                "status": _main.JOB_STATUS.get(job_id),
            }

        before = snapshot()
        reset = run_real_projects_reset("no-character")
        assert reset["after"]["projectsState"]["projectId"] == "a" * 32
        assert all("/run" not in path for path in reset["requests"])
        assert snapshot() == before
    finally:
        generator.close()

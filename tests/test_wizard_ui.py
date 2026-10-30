# SPDX-License-Identifier: MIT
"""First-run wizard contract: gating, steps, connection test/save, tour, and page wiring."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
NODE = Path("/opt/homebrew/opt/node@22/bin/node")

HARNESS = r'''
const fs = require('fs');
const vm = require('vm');
const script = process.argv[1];
const action = process.argv[2];

function makeElement(id) {
  return {id, hidden: false, disabled: false, value: '', textContent: '', placeholder: '',
    type: '', children: [], listeners: {}, dataset: {}, className: '', style: {},
    classList: {add(name) { this.names.add(name); }, remove(name) { this.names.delete(name); },
      toggle(name, on) { on ? this.names.add(name) : this.names.delete(name); }, names: new Set()},
    setAttribute(name, value) { this['attr_' + name] = value; },
    append(...nodes) { this.children.push(...nodes); },
    addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); },
    dispatchEvent(event) { (this.listeners[event.type] || []).forEach((handler) => handler(event)); },
    click() { (this.listeners.click || []).forEach((handler) => handler({type: 'click'})); },
    scrollIntoView() {}, getBoundingClientRect() { return {top: 10, left: 10, bottom: 60, right: 300, width: 290, height: 50}; }};
}
const ids = ['wizard', 'wizard-title', 'wizard-back', 'wizard-skip', 'wizard-next',
  'wizard-welcome', 'wizard-connection', 'wizard-tour', 'wizard-done', 'wizard-providers',
  'wizard-url', 'wizard-key', 'wizard-test', 'wizard-save', 'wizard-test-result',
  'wizard-lock-note', 'wizard-connection-note', 'wizard-start-tour', 'wizard-done-tour',
  'help-tour', 'tour-card', 'tour-count', 'tour-title', 'tour-body', 'tour-back',
  'tour-next', 'tour-exit', 'health-retry', 'backend', 'readiness', 'workflow-catalog',
  'source', 'reference_1', 'advanced', 'rights', 'submit'];
const byId = Object.fromEntries(ids.map((id) => [id, makeElement(id)]));
// The real markup ships the wizard and the tour card hidden.
byId['wizard'].hidden = true;
byId['tour-card'].hidden = true;
const progressDashes = [makeElement('dash1'), makeElement('dash2'), makeElement('dash3'), makeElement('dash4')];
const requests = [];
const storage = new Map();
const events = [];
let savedSettings = {comfy_url: 'http://127.0.0.1:8188', backend: 'dry_run', locked: [],
  has_api_key: false, api_key_hint: null, saved: false, backends: ['dry_run', 'legacy', 'sdk'],
  fields: {backend: {value: 'dry_run', locked: false, source: 'default'},
    comfy_url: {value: 'http://127.0.0.1:8188', locked: false, source: 'default'},
    comfy_api_key: {has_value: false, hint: null, locked: false, source: 'default'}}};
const document = {
  readyState: 'complete', listeners: {},
  getElementById: (id) => byId[id] || null,
  querySelector: (selector) => {
    if (selector.startsWith('#')) return byId[selector.slice(1)] || null;
    if (selector === '.steps') return byId['wizard'];  // stand-in with class hooks
    return null;
  },
  querySelectorAll: (selector) => selector === '#wizard-progress li' ? progressDashes : [],
  createElement: () => makeElement('generated'),
  dispatchEvent(event) { events.push(event.type); (this.listeners[event.type] || []).forEach((handler) => handler(event)); },
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); },
};
async function fetch(path, options = {}) {
  requests.push({path, method: options.method || 'GET', body: options.body ? JSON.parse(options.body) : null});
  if (path === '/api/settings' && (!options.method || options.method === 'GET')) {
    return {ok: true, json: async () => savedSettings};
  }
  if (path === '/api/settings' && options.method === 'POST') {
    return {ok: true, status: 200, json: async () => ({...savedSettings, message: 'Dry run is local only.'})};
  }
  if (path === '/api/settings/test') {
    return {ok: true, status: 200, json: async () => ({ok: true, code: 'local_dry_run', message: 'Dry run is local only and performs no AI inference or renderer connection.'})};
  }
  return {ok: false, status: 404, json: async () => ({detail: 'unexpected ' + path})};
}
const context = {console, document, fetch, CustomEvent, FormData, setInterval: () => 0, clearInterval: () => {},
  localStorage: {getItem: (key) => storage.get(key) || null, setItem: (key, value) => storage.set(key, String(value)),
    removeItem: (key) => storage.delete(key)}};
context.window = context;
context.matchMedia = () => ({matches: true});
context.addEventListener = () => {};
if (action === 'already-done' || action === 'help-button') storage.set('recastroom.setupDone', '1');
if (action === 'automated') context.navigator = {webdriver: true};
vm.runInContext(fs.readFileSync(script, 'utf8'), vm.createContext(context), {filename: script});
async function settle() { for (let index = 0; index < 24; index += 1) await Promise.resolve(); }
const output = {requests, events, storage: Object.fromEntries(storage.entries()), healthRetryClicks: 0};
const healthRetry = byId['health-retry'];
healthRetry.listeners.click = [() => { output.healthRetryClicks += 1; }];

async function run() {
  if (action === 'first-run') {
    await settle();
    output.wizardHidden = byId['wizard'].hidden;
    output.welcomeHidden = byId['wizard-welcome'].hidden;
    output.connectionHidden = byId['wizard-connection'].hidden;
    output.title = byId['wizard-title'].textContent;
  } else if (action === 'walk') {
    await settle();
    byId['wizard-next'].click();            // welcome -> connection
    await settle();
    output.providers = byId['wizard-providers'].children.map((child) => child.dataset.backend);
    output.activeProvider = byId['wizard-providers'].children
      .filter((child) => child.className.includes('active')).map((child) => child.dataset.backend);
    output.urlPlaceholder = byId['wizard-url'].placeholder;
    byId['wizard-test'].click();
    await settle();
    output.testCallout = {hidden: byId['wizard-test-result'].hidden, className: byId['wizard-test-result'].className};
    byId['wizard-save'].click();
    await settle();
    output.saveCallout = byId['wizard-test-result'].textContent;
    output.saveRequest = requests.find((request) => request.path === '/api/settings' && request.method === 'POST') || null;
    byId['wizard-next'].click();            // connection -> tour
    await settle();
    output.tourPaneHidden = byId['wizard-tour'].hidden;
    byId['wizard-next'].click();            // start tour
    await settle();
    output.tourCardHidden = byId['tour-card'].hidden;
    output.tourTitle = byId['tour-title'].textContent;
    output.wizardHiddenDuringTour = byId['wizard'].hidden;
    for (let index = 0; index < 8; index += 1) { byId['tour-next'].click(); await settle(); }
    output.doneStorage = storage.get('recastroom.setupDone');
    output.wizardHiddenAfter = byId['wizard'].hidden;
  } else if (action === 'skip') {
    await settle();
    byId['wizard-skip'].click();
    await settle();
    output.skippedStorage = storage.get('recastroom.setupDone');
    output.wizardHidden = byId['wizard'].hidden;
  } else if (action === 'already-done') {
    await settle();
    output.wizardHiddenOnLoad = byId['wizard'].hidden;
  } else if (action === 'automated') {
    await settle();
    output.wizardHiddenOnLoad = byId['wizard'].hidden;
    output.storageAfterLoad = storage.get('recastroom.setupDone') || null;
  } else if (action === 'help-button') {
    await settle();
    byId['help-tour'].click();
    await settle();
    output.openedAtTour = !byId['wizard-tour'].hidden && byId['wizard'].hidden === false;
    output.title = byId['wizard-title'].textContent;
  }
  await settle();
  console.log(JSON.stringify(output));
}
run().catch((error) => { console.error(String(error)); process.exit(1); });
'''


def run_harness(action: str) -> dict:
    result = subprocess.run(
        [str(NODE), "-e", HARNESS, str(ROOT / "app/web/wizard.js"), action],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_first_run_opens_wizard_at_welcome() -> None:
    state = run_harness("first-run")
    assert state["wizardHidden"] is False
    assert state["welcomeHidden"] is False
    assert state["connectionHidden"] is True
    assert state["title"] == "Welcome to RecastRoom"


def test_walk_connection_test_save_and_tour() -> None:
    state = run_harness("walk")
    assert state["providers"] == ["dry_run", "legacy", "sdk"]
    assert state["activeProvider"] == ["dry_run"]
    assert state["urlPlaceholder"] == "http://127.0.0.1:8188"
    assert state["testCallout"]["hidden"] is False
    assert "ok" in state["testCallout"]["className"]
    assert "saved and in use" in state["saveCallout"]
    save = state["saveRequest"]
    assert save is not None and save["body"]["backend"] == "dry_run"
    assert state["healthRetryClicks"] >= 1
    assert state["tourPaneHidden"] is False
    assert state["wizardHiddenDuringTour"] is True
    assert state["tourCardHidden"] is False
    assert state["tourTitle"] == "Four steps, one desk"
    assert state["doneStorage"] == "1"
    assert state["wizardHiddenAfter"] is True


def test_skip_marks_setup_done() -> None:
    state = run_harness("skip")
    assert state["skippedStorage"] == "1"
    assert state["wizardHidden"] is True


def test_completed_setup_does_not_reopen() -> None:
    state = run_harness("already-done")
    assert state["wizardHiddenOnLoad"] is True


def test_automated_browser_sessions_skip_the_first_run_wizard() -> None:
    """The evidence journeys (Playwright) must find the plain desk, not a modal."""
    state = run_harness("automated")
    assert state["wizardHiddenOnLoad"] is True
    # Skipped for automation, not recorded as completed for a human visitor.
    assert state["storageAfterLoad"] is None


def test_help_button_reopens_at_tour() -> None:
    state = run_harness("help-button")
    assert state["openedAtTour"] is True
    assert state["title"] == "A quick look around"


def test_wizard_markup_is_wired_into_the_workspace_page() -> None:
    page = (ROOT / "app/web/index.html").read_text(encoding="utf-8")
    for anchor in (
        'id="wizard"', 'id="wizard-progress"', 'id="wizard-connection"', 'id="wizard-providers"',
        'id="wizard-url"', 'id="wizard-key"', 'id="wizard-test"', 'id="wizard-save"',
        'id="wizard-test-result"', 'id="wizard-start-tour"', 'id="tour-card"', 'id="tour-next"',
        'id="help-tour"', 'href="/studio.css"', 'src="/wizard.js',
    ):
        assert anchor in page, anchor
    # The moved status controls exist exactly once each.
    assert page.count('id="backend"') == 1
    assert page.count('id="health-retry"') == 1
    assert page.count('id="readiness"') == 1
    # The studio layout wraps the rail and the flow.
    assert 'class="studio-layout"' in page and 'class="studio-rail"' in page and 'class="studio-flow"' in page


def test_workspace_page_serves_the_new_layer() -> None:
    from fastapi.testclient import TestClient as Client

    import app.main as main

    client = Client(main.app)
    page = client.get("/")
    assert page.status_code == 200
    assert "/studio.css" in page.text and "/wizard.js" in page.text
    stylesheet = client.get("/studio.css")
    assert stylesheet.status_code == 200
    script = client.get("/wizard.js")
    assert script.status_code == 200

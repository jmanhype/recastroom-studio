# SPDX-License-Identifier: MIT
"""Native M1 browser journey across real restarts, worker, and export bytes."""
from __future__ import annotations

import hashlib, json, os, socket, sqlite3, subprocess
from pathlib import Path
import sys
from textwrap import dedent
from openjutsu.m1_types import Timebase, AttemptEvent, AttemptState as S, ExecutionMode as M, public_json
from openjutsu.take_service import TakeService
from openjutsu.workspace_store import WorkspaceStore
from tools.foundation_runtime import FFMPEG, FFPROBE, FoundationServer, free_loopback_port, generate_media


BROWSER_PYTHON = Path(sys.executable)


def _browser_program() -> str:
    return dedent(
        """
        import hashlib, json, sqlite3, sys
        from pathlib import Path
        from urllib.parse import urlsplit
        from playwright.sync_api import sync_playwright

        mode, base_url, evidence_root, workspace = sys.argv[1:5]
        evidence_root = Path(evidence_root); evidence_root.mkdir(parents=True, exist_ok=True)
        requests, console_errors, resource_errors = [], [], []

        def public_request(request):
            parsed = urlsplit(request.url)
            assert not parsed.username and not parsed.password
            assert not any(key in parsed.query.lower() for key in ('token=', 'secret=', 'key='))
            requests.append({'method': request.method, 'url': request.url,
                             'origin': f'{parsed.scheme}://{parsed.netloc}', 'path': parsed.path})

        def public_response(response):
            if response.url.startswith(base_url + '/') and response.status >= 400:
                resource_errors.append({'status': response.status, 'path': '/' + response.url.split('/', 3)[-1]})

        def state(page):
            return page.evaluate('() => ({projects: window.ProjectsUI.getState(), m1: window.M1UI.getState()})')

        def select_workspace(page, project_id, character):
            page.select_option('#project-select', project_id)
            page.wait_for_function("() => window.ProjectsUI?.getState?.().projectId")
            page.select_option('#character-select', character)
            page.wait_for_function("() => window.ProjectsUI?.getReferenceState?.().ready")
            page.wait_for_function("() => window.M1UI.getState().scenes.length > 0")
            page.select_option('#m1-scene-select', page.evaluate(
                "() => window.M1UI.getState().scenes[0].id"
            ))

        def database_rows(workspace):
            database = Path(workspace) / 'workspace.sqlite3'
            with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as db:
                db.row_factory = sqlite3.Row
                attempts = [dict(row) for row in db.execute('SELECT * FROM attempts ORDER BY created_at,attempt_id')]
                takes = [dict(row) for row in db.execute('SELECT * FROM takes ORDER BY created_at,take_id')]
            return attempts, takes

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, channel='chrome',
                args=['--no-first-run', '--no-default-browser-check'],
            )
            context = browser.new_context(
                viewport={'width': 1440, 'height': 1200}, accept_downloads=True
            )
            page = context.new_page()
            page.on('request', public_request)
            page.on('pageerror', lambda error: console_errors.append(str(error)))
            page.on('response', public_response)
            page.goto(base_url, wait_until='domcontentloaded')
            evidence = {'mode': mode, 'consoleErrors': console_errors}

            if mode == 'phase1':
                source, primary, secondary = (Path(item) for item in sys.argv[5:8])
                page.fill('#project-name', 'M1 native capstone')
                page.click('#create-project')
                page.wait_for_function("() => window.ProjectsUI?.getState?.().projectId")
                page.locator('#character-editor > summary').click()
                page.fill('#character-name', 'Journey performer')
                page.set_input_files('#character-reference-1', primary)
                page.set_input_files('#character-reference-2', secondary)
                page.click('#create-character')
                page.wait_for_function("() => document.getElementById('character-note').textContent.includes('ready for reuse')")
                page.set_input_files('#m1-source', source)
                page.click('#m1-upload')
                page.wait_for_function("() => document.getElementById('m1-source-note').textContent.includes('Source inspected')")
                rows = page.locator('.archive-search')
                for shot_id, start, end, kind in (
                    ('shot-a', '0', '8', 'render'), ('shot-b', '8', '16', 'render'),
                    ('shot-c', '16', '24', 'pass_through'),
                ):
                    if shot_id != 'shot-a': page.click('#m1-add-shot')
                    row = rows.nth({'shot-a': 0, 'shot-b': 1, 'shot-c': 2}[shot_id])
                    row.locator('input').nth(0).fill(shot_id)
                    row.locator('input').nth(1).fill(start)
                    row.locator('input').nth(2).fill(end)
                    row.locator('select').select_option(kind)
                page.click('#m1-confirm')
                page.wait_for_function("() => document.getElementById('m1-cut-note').textContent.includes('Confirmed immutable revision 1')")
                evidence['initialState'] = state(page)
                assert evidence['initialState']['m1']['sourceTiming']['frame_count'] == 24
                assert evidence['initialState']['m1']['scenes'][0]['shots'] == [
                    {'id': 'shot-a', 'source_range': {'start': 0, 'end': 8}, 'kind': 'render'},
                    {'id': 'shot-b', 'source_range': {'start': 8, 'end': 16}, 'kind': 'render'},
                    {'id': 'shot-c', 'source_range': {'start': 16, 'end': 24}, 'kind': 'pass_through'},
                ]
                assert not any(item['path'].endswith('/attempts') and item['method'] == 'POST'
                               for item in requests)
                page.screenshot(path=str(evidence_root / '01-source-cuts.png'), full_page=True)
            elif mode == 'phase2':
                phase1 = json.loads((evidence_root / 'phase1.json').read_text())
                project = phase1['initialState']['projects']['projectId']
                scene_id = phase1['initialState']['m1']['scenes'][0]['id']
                character = phase1['initialState']['projects']['characterId'] + ':' + str(
                    phase1['initialState']['projects']['characterVersion']
                )
                select_workspace(page, project, character)
                page.wait_for_function("() => window.M1UI.getState().attempts.length === 0")
                timing = phase1['initialState']['m1']['sourceTiming']
                word_input = {'source_asset_id': timing['asset_id'], 'source_sha256': timing['sha256'],
                              'words': [{'start': 9/24, 'end': 10/24, 'word': 'hello'}]}
                word_path = evidence_root / 'original-word-timing.json'
                word_path.write_text(json.dumps(word_input))
                page.set_input_files('#m1-word-timing', word_path)
                page.wait_for_function("() => window.M1UI.getState().wordTiming !== null")
                operations = {}
                for shot_id in ('shot-a', 'shot-b'):
                    page.select_option('#m1-shot-select', shot_id)
                    attempts_before_refusal = page.evaluate('() => window.M1UI.getState().attempts.length')
                    page.uncheck('#m1-rights')
                    page.click('#m1-resolve')
                    page.wait_for_function("() => document.getElementById('m1-resolve-note').textContent.includes('Resolution refused')")
                    assert page.evaluate('() => window.M1UI.getState().attempts.length') == attempts_before_refusal
                    page.check('#m1-rights')
                    page.click('#m1-resolve')
                    page.wait_for_function("() => document.getElementById('m1-resolve-note').textContent.includes('No execution attempt')")
                    operation = page.evaluate('() => window.M1UI.getState().resolvedOperation')
                    page.check('#m1-authorize-rights')
                    page.click('#m1-authorize')
                    page.wait_for_function("operationId => window.M1UI.getState().attempts.some(item => item.operation_id === operationId && item.state === 'prepared')", arg=operation['id'])
                    page.click('#m1-authorize')
                    page.wait_for_function("operationId => window.M1UI.getState().attempts.filter(item => item.operation_id === operationId).length === 1", arg=operation['id'])
                    operations[shot_id] = operation
                evidence['operations'] = operations
                evidence['attemptsAfterDuplicateAuthorization'] = page.evaluate('() => window.M1UI.getState().attempts')
                assert len(evidence['attemptsAfterDuplicateAuthorization']) == 2
                assert all(item['state'] == 'prepared' for item in evidence['attemptsAfterDuplicateAuthorization'])
                page.screenshot(path=str(evidence_root / '02-cpu-dry-runs.png'), full_page=True)
            elif mode == 'phase3':
                phase1 = json.loads((evidence_root / 'phase1.json').read_text())
                project = phase1['initialState']['projects']['projectId']
                character = phase1['initialState']['projects']['characterId'] + ':' + str(
                    phase1['initialState']['projects']['characterVersion']
                )
                select_workspace(page, project, character)
                page.wait_for_function("() => window.M1UI.getState().attempts.filter(item => item.state === 'completed').length === 2")
                attempts, takes = database_rows(workspace)
                operations = json.loads((evidence_root / 'phase2.json').read_text())['operations']
                pending = json.loads((evidence_root / 'phase2.json').read_text())['attemptsAfterDuplicateAuthorization']
                assert {item['id'] for item in pending} == {item['attempt_id'] for item in attempts}
                with sqlite3.connect(f'file:{Path(workspace) / "workspace.sqlite3"}?mode=ro', uri=True) as db:
                    recovered_receipts = db.execute('SELECT attempt_id,receipt_sha256 FROM provider_receipts').fetchall()
                assert {item[0] for item in recovered_receipts} == {item['id'] for item in pending}
                evidence['recoveredReceipts'] = recovered_receipts
                original = next(item for item in takes if item['shot_id'] == 'shot-b')
                page.select_option('#m1-shot-select', 'shot-b')
                page.set_input_files('#m1-word-timing', evidence_root / 'original-word-timing.json')
                page.wait_for_function("() => window.M1UI.getState().wordTiming !== null")
                page.check('#m1-rights')
                page.click('#m1-resolve')
                page.wait_for_function("() => document.getElementById('m1-resolve-note').textContent.includes('No execution attempt')")
                operation = page.evaluate('() => window.M1UI.getState().resolvedOperation')
                page.select_option('#m1-review-shot', 'shot-b')
                page.select_option('#m1-mode', 'dry_run')
                page.select_option('#m1-incumbent-select', original['take_id'])
                page.check('#m1-challenger-rights')
                with page.expect_response(lambda response: response.request.method == 'POST' and response.url.endswith('/attempts')) as response:
                    page.click('#m1-challenger-authorize')
                assert response.value.status == 201
                challenge = response.value.json()
                assert challenge['challenger_of'] == original['attempt_id']
                assert challenge['mode'] == 'dry_run' and challenge['operation_id'] == operation['id']
                page.wait_for_function("id => window.M1UI.getState().attempts.some(a => a.id === id && a.state === 'completed')", arg=challenge['id'])
                with page.expect_response(lambda response: response.request.method == 'POST' and response.url.endswith('/attempts')) as duplicate:
                    page.click('#m1-challenger-authorize')
                assert duplicate.value.status == 200 and duplicate.value.json()['id'] == challenge['id']
                after = database_rows(workspace)[1]
                assert {item['take_id']: item for item in after if item['take_id'] in {t['take_id'] for t in takes}} == {item['take_id']: item for item in takes}
                assert len(after) == len(takes) + 1
                evidence.update({
                    'challenge': challenge, 'duplicateChallenge': duplicate.value.json(),
                    'challengeResponseStatuses': [response.value.status, duplicate.value.status], 'knownIdRecovery': pending,
                    'before': {'attempts': attempts, 'takes': takes},
                    'after': {'takes': after},
                })
                page.screenshot(path=str(evidence_root / '03-challenger-truthful-cancel.png'), full_page=True)
            elif mode == 'phase4':
                phase1 = json.loads((evidence_root / 'phase1.json').read_text())
                project = phase1['initialState']['projects']['projectId']
                scene_id = phase1['initialState']['m1']['scenes'][0]['id']
                character = phase1['initialState']['projects']['characterId'] + ':' + str(
                    phase1['initialState']['projects']['characterVersion']
                )
                select_workspace(page, project, character)
                page.wait_for_function("() => window.M1UI.getState().attempts.filter(item => item.state === 'completed').length === 3")
                page.select_option('#m1-shot-select', 'shot-a')
                page.fill('#m1-seed', '118')
                page.check('#m1-rights')
                page.click('#m1-resolve')
                page.wait_for_function("() => document.getElementById('m1-resolve-note').textContent.includes('No execution attempt')")
                page.select_option('#m1-mode', 'dry_run')
                page.check('#m1-authorize-rights')
                page.click('#m1-authorize')
                page.wait_for_function("() => window.M1UI.getState().attempts.some(a => a.state === 'prepared')")
                queued = next(item for item in state(page)['m1']['attempts'] if item['state'] == 'prepared')
                assert 'Queued prevention' in page.locator('#m1-attempts').inner_text()
                page.click('#m1-cancel')
                page.wait_for_function("id => window.M1UI.getState().attempts.some(a => a.id === id && a.state === 'provider_confirmed_cancelled')", arg=queued['id'])
                evidence['queuedCancellation'] = {'attempt': queued, 'boundary': 'local queued prevention, not remote provider cancellation'}
                page.screenshot(path=str(evidence_root / '06-queued-cancel.png'), full_page=True)
                before_reads = len(requests)
                saved_takes = database_rows(workspace)[1]
                page.click('#reset')
                page.wait_for_function("() => window.M1UI.getState().scenes.length === 1")
                assert state(page)['m1']['wordTiming'] is None
                assert database_rows(workspace)[1] == saved_takes
                page.reload(wait_until='domcontentloaded')
                select_workspace(page, project, character)
                page.evaluate('() => window.M1UI.refresh()')
                page.wait_for_function("() => window.M1UI.getState().scenes.length === 1")
                assert not any(r['method'] == 'POST' and r['path'].endswith('/attempts') for r in requests[before_reads:])
                evidence['resetRefresh'] = {'takesUnchanged': True, 'attemptPosts': 0}
                page.screenshot(path=str(evidence_root / '07-durable-reset.png'), full_page=True)
                downloads = []
                page.on('download', lambda download: downloads.append(download.suggested_filename))
                page.click('#m1-create-edit')
                page.wait_for_function("() => document.getElementById('m1-export-status').textContent.includes('refused')")
                assert not downloads and page.locator('#m1-export-download').is_hidden()
                with sqlite3.connect(f'file:{Path(workspace) / "workspace.sqlite3"}?mode=ro', uri=True) as db:
                    assert db.execute('SELECT COUNT(*) FROM exports').fetchone()[0] == 0
                    assert db.execute('SELECT COUNT(*) FROM edit_revisions').fetchone()[0] == 0
                evidence['missingTakeRefusal'] = page.locator('#m1-export-status').inner_text()
                page.screenshot(path=str(evidence_root / '08-missing-take-refusal.png'), full_page=True)
                page.locator('#m1-export-status').screenshot(path=str(evidence_root / '08-refusal-detail.png'))
                database = Path(workspace) / 'workspace.sqlite3'
                replay_takes = {}
                uploads = {}
                with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as db:
                    db.row_factory = sqlite3.Row
                    db.execute('SELECT asset_id FROM assets WHERE role=?', ('source',)).fetchone()
                    for shot_id in ('shot-a', 'shot-b'):
                        row = db.execute('''SELECT t.*,o.window_json,o.pin_json,o.canonical_json FROM takes t JOIN operations o USING(operation_id) JOIN attempts a ON(a.attempt_id=t.attempt_id) WHERE t.shot_id=? AND t.origin=? AND a.state=?''', (shot_id, 'dry_run', 'completed')).fetchone()
                        output = db.execute('SELECT relative_path,root_kind FROM assets WHERE asset_id=?', (row['output_asset_id'],)).fetchone()
                        root = 'imports' if output['root_kind'] == 'imports' else 'uploads'
                        output_path = Path(workspace) / root / output['relative_path']
                        manifest = json.loads(row['canonical_json'])
                        pin = json.loads(row['pin_json'])
                        receipt = {
                            'scene_revision_id': row['scene_revision_id'],
                            'shot_id': shot_id,
                            'source_sha256': manifest['source']['sha256'],
                            'input_sha256': manifest['source']['proxy_sha256'],
                            'recipe_id': pin['recipe_id'],
                            'recipe_version': pin['version'],
                            'raw_graph_sha256': pin['raw_graph_sha256'],
                            'resolved_graph_sha256': manifest['graph']['resolved_semantic_sha256'],
                            'output_sha256': row['output_sha256'],
                            'window': json.loads(row['window_json']),
                            'historical_verdict': 'keeper',
                        }
                        receipt_path = evidence_root / f'{shot_id}-replay-receipt.json'
                        receipt_path.write_text(json.dumps(receipt))
                        page.set_input_files('#m1-replay-file', output_path)
                        page.set_input_files('#m1-replay-receipt', receipt_path)
                        with page.expect_response(lambda response: response.url.endswith('/replay-import')) as response:
                            page.click('#m1-replay-import')
                        uploaded = {'status': response.value.status, 'body': response.value.json()}
                        assert uploaded['status'] == 201, uploaded
                        page.wait_for_function("() => document.getElementById('m1-replay-status').textContent.includes('imported')")
                        assert 'historical' in page.locator('#m1-replay-lineage').inner_text().lower()
                        replay_takes[shot_id] = uploaded['body']
                        uploads[shot_id] = {'receipt': receipt, 'response': uploaded}
                page.evaluate('async () => { await window.M1UI.refresh(); }')
                page.wait_for_function("() => document.querySelectorAll('#m1-takes li').length >= 2")
                selection_revisions = {}
                for shot_id in ('shot-a', 'shot-b'):
                    page.select_option('#m1-review-shot', shot_id)
                    page.wait_for_function("count => document.querySelectorAll('#m1-takes li').length === count", arg=2 if shot_id == 'shot-a' else 3)
                    page.get_by_role('button', name='Compare synchronized').last.click()
                    page.wait_for_function("() => document.getElementById('m1-comparison-preview').readyState >= 2")
                    page.fill('#m1-review-note', f'human keeper review for {shot_id}')
                    page.select_option('#m1-review-verdict', 'keeper')
                    page.click('#m1-review-append')
                    page.wait_for_function("() => document.getElementById('m1-review-note-status').textContent.includes('Human review keeper appended')")
                    page.get_by_role('button', name='Select candidate').last.click()
                    page.wait_for_function("() => document.getElementById('m1-review-note-status').textContent.includes('Durable selection revision')")
                    selection_revisions[shot_id] = page.evaluate('() => window.M1UI.getState().selectionRevision')
                    if shot_id == 'shot-a':
                        selection_actions = []
                        for label in ('Select candidate', 'Deselect', 'Select candidate'):
                            with page.expect_response(lambda response: response.request.method == 'PUT' and response.url.endswith('/selection')) as response:
                                if label == 'Deselect': page.click('#m1-deselect')
                                else: page.get_by_role('button', name=label).last.click()
                            assert response.value.status == 200
                            selection_actions.append(response.value.json())
                            page.wait_for_function("revision => window.M1UI.getState().selectionRevision === revision", arg=selection_actions[-1]['revision'])
                        assert [item['revision'] for item in selection_actions] == [2, 3, 4]
                        assert [item['take_id'] for item in selection_actions] == [replay_takes[shot_id]['id'], None, replay_takes[shot_id]['id']]
                        evidence['shotASelectionOperations'] = selection_actions
                        selection_revisions['shot-a-reselect-deselect-select'] = 4
                page.select_option('#m1-review-shot', 'shot-a')
                page.get_by_role('button', name='Select candidate').last.click()
                page.wait_for_function("() => document.getElementById('m1-review-note-status').textContent.includes('Selection conflict visible')")
                page.evaluate('async () => { await window.M1UI.refresh(); }')
                page.wait_for_function("() => document.querySelectorAll('.m1-export-row').length === 3")

                def export_row(value):
                    for row in page.locator('.m1-export-row').all():
                        if row.locator('[data-export-field=shot]').input_value() == value:
                            return row
                    raise AssertionError(f'export row {value} not found')

                export_row('shot-c').get_by_role('button', name='Earlier').click()
                export_row('shot-c').get_by_role('button', name='Earlier').click()
                export_row('shot-b').get_by_role('button', name='Earlier').click()
                for shot_id, start, end, keep_start, keep_end in (
                    ('shot-a', 1, 5, 1, 5), ('shot-b', 10, 14, 2, 6),
                ):
                    row = export_row(shot_id)
                    row.locator('[data-export-field=take]').select_option(replay_takes[shot_id]['id'])
                    row.locator('[data-export-field=source-start]').fill(str(start))
                    row.locator('[data-export-field=source-end]').fill(str(end))
                    row.locator('[data-export-field=keep-start]').fill(str(keep_start))
                    row.locator('[data-export-field=keep-end]').fill(str(keep_end))
                assert export_row('shot-c').locator('[data-export-field=take]').input_value() == ''
                page.select_option('#m1-audio-policy', 'source_edit_map')
                page.click('#m1-create-edit')
                page.wait_for_function("() => document.getElementById('m1-export-status').textContent.includes('Frozen edit revision')")
                page.click('#m1-export')
                page.wait_for_function("() => document.getElementById('m1-export-status').textContent.includes('Export completed')")
                with page.expect_download() as download_info:
                    page.click('#m1-export-download')
                download = download_info.value
                destination = evidence_root / 'actual-download.mp4'
                download.save_as(destination)
                evidence.update({
                    'replayUploads': uploads,
                    'replayTakes': replay_takes,
                    'selectionRevisions': selection_revisions,
                    'finalState': state(page),
                    'download': {
                        'filename': download.suggested_filename,
                        'bytes': destination.stat().st_size,
                        'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                    },
                })
                page.screenshot(path=str(evidence_root / '04-review-selection.png', ), full_page=True)
                page.screenshot(path=str(evidence_root / '05-export-download.png'), full_page=True)
            elif mode == 'safety':
                phase1 = json.loads((evidence_root / 'phase1.json').read_text())
                project = phase1['initialState']['projects']['projectId']
                character = phase1['initialState']['projects']['characterId'] + ':' + str(phase1['initialState']['projects']['characterVersion'])
                select_workspace(page, project, character)
                page.wait_for_function("() => window.M1UI.getState().attempts.some(a => a.state === 'reconcile_needed')")
                unknown = next(item for item in state(page)['m1']['attempts'] if item['state'] == 'reconcile_needed')
                visible = page.locator('#m1-attempts').inner_text()
                assert 'Paused unknown outcome' in visible and unknown['id'] in visible
                assert 'reconciliation is required before any conclusion or retry' in visible
                evidence['unknown'] = {'fixture': 'OFFLINE presentation fixture; fenced DB transition, not provider lookup/recovery/refund', 'attempt': unknown, 'visible': visible}
                page.screenshot(path=str(evidence_root / '09-offline-paused-unknown.png'), full_page=True)
                page.locator('#m1-attempts').screenshot(path=str(evidence_root / '09-paused-detail.png'))
                page.set_input_files('#m1-word-timing', evidence_root / 'original-word-timing.json')
                page.wait_for_function("() => window.M1UI.getState().wordTiming !== null")
                page.fill('#project-name', 'Independent empty race project')
                page.click('#create-project')
                page.wait_for_function("old => window.ProjectsUI.getState().projectId !== old", arg=project)
                second = state(page)['projects']['projectId']
                assert state(page)['m1']['wordTiming'] is None
                held = []
                def delay_actual_response(route):
                    response = route.fetch()
                    assert response.status == 200
                    held.append((route, response))
                page.route(base_url + '/api/projects/' + project + '/scenes', delay_actual_response)
                page.select_option('#project-select', project)
                for _ in range(200):
                    if held: break
                    page.wait_for_timeout(25)
                assert held, 'actual old-project GET was not observed'
                page.select_option('#project-select', second)
                page.wait_for_function("id => window.ProjectsUI.getState().projectId === id && window.M1UI.getState().scenes.length === 0", arg=second)
                for route, response in held: route.fulfill(response=response)
                page.unroute(base_url + '/api/projects/' + project + '/scenes', delay_actual_response)
                page.wait_for_timeout(300)
                assert state(page)['projects']['projectId'] == second and state(page)['m1']['scenes'] == []
                evidence['staleProjectRace'] = {'delayedActualResponses': len(held), 'oldProject': project, 'visibleProject': second, 'stateAfterDelivery': state(page)}
                page.screenshot(path=str(evidence_root / '10-real-stale-project-race.png'), full_page=True)
                select_workspace(page, project, character)
                page.wait_for_function("() => window.M1UI.getState().attempts.some(a => a.state === 'reconcile_needed')")
                assert next(a for a in state(page)['m1']['attempts'] if a['id'] == unknown['id']) == unknown
                assert not any(r['method'] == 'POST' and r['path'].endswith('/attempts') for r in requests)
            else:
                raise AssertionError(f'unknown browser phase {mode}')

            evidence['requests'] = requests
            evidence['resourceErrors'] = resource_errors
            evidence['nonLocalRequests'] = [item for item in requests if item['origin'] != base_url]
            assert requests and any(item['path'].endswith('/scenes') for item in requests)
            assert evidence['nonLocalRequests'] == []
            assert console_errors == [], console_errors
            assert all(
                item == {'status': 404, 'path': '/favicon.ico'}
                or (item['status'] == 422 and item['path'].endswith('/operations/resolve'))
                or (item['status'] == 409 and '/selection' in item['path'])
                or (item['status'] == 422 and item['path'].endswith('/edit-revisions'))
                for item in resource_errors
            ), resource_errors
            (evidence_root / f'{mode}.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\\n', encoding='utf-8')
            context.close()
            browser.close()
        """
    )


def _run_browser(mode: str, base_url: str, evidence: Path, workspace: Path,
                 *extra: Path, timeout: int = 180) -> None:
    command = [str(BROWSER_PYTHON), "-", mode, base_url, str(evidence), str(workspace), *map(str, extra)]
    result = subprocess.run(command, input=_browser_program(), text=True, timeout=timeout, capture_output=True)
    assert result.returncode == 0, result.stderr


def _raw_pixels(path: Path, start: int, end: int) -> bytes:
    args = [str(FFMPEG), "-nostdin", "-loglevel", "error", "-i", str(path), "-vf",
            f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS", "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1"]
    return subprocess.run(args, check=True, capture_output=True, timeout=30).stdout


def _assert_pixels(actual: bytes, expected: bytes) -> None:
    assert len(actual) == len(expected)
    frame_bytes = len(expected) // 16
    for frame in range(16):
        left, right = actual[frame * frame_bytes:(frame + 1) * frame_bytes], expected[frame * frame_bytes:(frame + 1) * frame_bytes]
        mean, outliers = sum(abs(a - b) for a, b in zip(left, right)) / frame_bytes, sum(abs(a - b) > 32 for a, b in zip(left, right)) / frame_bytes
        assert mean < 5 and outliers < 0.01, frame


def _counts(database: Path) -> dict[str, int]:
    tables = ("attempts", "takes", "qualified_replay_receipts", "reviews", "selection_events", "edit_revisions", "exports")
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
        return {table: int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in tables}


def _offline_unknown_fixture(workspace: Path, operation_json: dict) -> None:
    """Accepted fenced offline presentation fixture; never live provider proof."""
    store = WorkspaceStore(workspace)
    operation = store.get_operation(operation_json['project_id'], operation_json['id'])
    unknown = store.authorize_attempt(operation, 'explicit-offline-presentation', M.DRY_RUN, None)
    with store.worker_lock('offline-presentation'):
        fence = store.claim_attempt('offline-presentation')
        assert fence is not None and fence.attempt_id == unknown.id
        for before, after in ((S.PREPARED, S.READY), (S.READY, S.SUBMITTING), (S.SUBMITTING, S.RECONCILE_NEEDED)):
            store.transition_attempt(fence, before, AttemptEvent(after.value, '{}'))


def _assert_teardown(servers: tuple[FoundationServer, ...]) -> list[dict]:
    """Measure closed local listeners after each owned process was waited for."""
    receipts = []
    for server in servers:
        assert server.process is None
        with socket.socket() as client:
            client.settimeout(1)
            assert client.connect_ex(('127.0.0.1', int(server.base_url.rsplit(':', 1)[1]))) != 0
        receipts.append({'origin': server.base_url, 'process_stopped': True, 'listener_closed': True})
    return receipts


def test_real_chrome_m1_journey_restart_worker_replay_review_and_export(tmp_path: Path):
    evidence = Path(os.environ.get("OJ_VQYG_EVIDENCE", str(tmp_path)))
    evidence.mkdir(parents=True, exist_ok=True)
    workspace = tmp_path / "workspace"
    media = generate_media(tmp_path / "input")
    server_one = FoundationServer(free_loopback_port(), workspace, evidence / "server-1.log"); server_one.start()
    try: _run_browser("phase1", server_one.base_url, evidence, workspace, media["source"], media["primary"], media["secondary"])
    finally: server_one.stop()
    database = workspace / "workspace.sqlite3"
    restart_one_hash = hashlib.sha256(database.read_bytes()).hexdigest()
    restart_one_counts = _counts(database)

    server_two = FoundationServer(free_loopback_port(), workspace, evidence / "server-2.log", test_lifespan="off"); server_two.start()
    try:
        restart_two_read_hash = hashlib.sha256(database.read_bytes()).hexdigest()
        restart_two_read_counts = _counts(database)
        _run_browser("phase2", server_two.base_url, evidence, workspace)
    finally: server_two.stop()
    restart_two_post_counts = _counts(database)

    restart_three_read_counts = _counts(database)
    server_three = FoundationServer(free_loopback_port(), workspace, evidence / "server-3.log"); server_three.start()
    try:
        restart_three_read_hash = hashlib.sha256(database.read_bytes()).hexdigest()
        _run_browser("phase3", server_three.base_url, evidence, workspace)
    finally: server_three.stop()

    server_four = FoundationServer(free_loopback_port(), workspace, evidence / "server-4.log", test_lifespan="off"); server_four.start()
    try: _run_browser("phase4", server_four.base_url, evidence, workspace, timeout=240)
    finally: server_four.stop()

    phase2 = json.loads((evidence / 'phase2.json').read_text())
    _offline_unknown_fixture(workspace, phase2['operations']['shot-a'])
    server_five = FoundationServer(free_loopback_port(), workspace, evidence / 'server-5.log', test_lifespan='off'); server_five.start()
    try: _run_browser('safety', server_five.base_url, evidence, workspace)
    finally: server_five.stop()
    teardown = _assert_teardown((server_one, server_two, server_three, server_four, server_five))

    phases = {name: json.loads((evidence / f"{name}.json").read_text()) for name in ("phase1", "phase2", "phase3", "phase4")}
    phase1, phase3, phase4 = phases["phase1"], phases["phase3"], phases["phase4"]
    project_id, scene_id = phase1["initialState"]["projects"]["projectId"], phase1["initialState"]["m1"]["scenes"][0]["id"]
    replay_ids = {shot: item["id"] for shot, item in phase4["replayTakes"].items()}
    store = WorkspaceStore(workspace)
    scene = store.get_scene_revision(project_id, scene_id)
    source_path = store.resolve_asset(scene.source.asset_id).path
    replay_paths = {shot: store.resolve_asset(store.get_take(project_id, take_id).output.asset_id).path for shot, take_id in replay_ids.items()}
    downloaded = evidence / "actual-download.mp4"
    final_hash = hashlib.sha256(downloaded.read_bytes()).hexdigest()
    export_record = phase4["finalState"]["m1"]["exportRecord"]
    assert final_hash == export_record["sha256"]
    assert TakeService._probe(downloaded)[:3] == (16, Timebase(1, 24), 0)
    expected_pixels = _raw_pixels(source_path, 16, 24) + _raw_pixels(replay_paths["shot-b"], 2, 6) + _raw_pixels(replay_paths["shot-a"], 1, 5)
    _assert_pixels(_raw_pixels(downloaded, 0, 16), expected_pixels)
    checks = json.loads(export_record["checks_json"])
    assert [item["shot_id"] for item in checks["edit_map"]["items"]] == [
        "shot-c", "shot-b", "shot-a"
    ]
    assert checks["audio"]["policy"] == "source_edit_map" and checks["audio"]["content"]["expected_samples"] == 32000
    assert checks["measurements"]["output_frames"] == 16 and checks["measurements"]["output_pts"] == 0
    assert checks["measurements"]["output_video_content"]["mean_absolute_error"] < 5
    assert checks["measurements"]["output_video_content"]["outlier_ratio"] < 0.01
    assert [item["timeline_start"] for item in checks["measurements"]["placement"]] == [0, 8, 12]

    clip_receipts = []
    for shot in ("shot-a", "shot-b"):
        take = store.get_take(project_id, replay_ids[shot])
        dry_rows = []
        with store._connect() as db:
            dry_rows = db.execute(
                """SELECT t.* FROM takes t JOIN attempts a USING(attempt_id)
                   WHERE t.shot_id=? AND t.origin=? ORDER BY t.created_at LIMIT 1""",
                (shot, "dry_run"),
            ).fetchall()
        dry = store.get_take(project_id, dry_rows[0]["take_id"])
        operation = store.get_operation(project_id, take.operation_id or "")
        manifest = json.loads(operation.canonical_json)
        binding = store.get_preparation_binding(project_id, operation.id)
        envelope = json.loads(store.resolve_asset(binding.binding_asset_id).path.read_bytes())
        canonical_words = envelope['word_timing']['canonical_content']
        word_sha = hashlib.sha256(canonical_words.encode()).hexdigest()
        assert canonical_words.endswith('\n') and word_sha == manifest['word_timing']['word_timing_sha256']
        assert json.loads(canonical_words)['segments'][0]['words'] == [{'start': 9/24, 'end': 10/24, 'word': 'hello'}]
        assert hashlib.sha256(public_json(manifest).encode()).hexdigest() == operation.fingerprint
        binding_asset = store.resolve_asset(binding.binding_asset_id)
        assert binding_asset.record.protected and hashlib.sha256(binding_asset.path.read_bytes()).hexdigest() == binding.binding_sha256
        assert envelope['operation_fingerprint'] == operation.fingerprint
        assert hashlib.sha256(envelope['word_schedule_content'].encode()).hexdigest() == manifest['prompt']['word_schedule_sha256']
        if shot == 'shot-b':
            assert 'frames 2-3 / 0.042-0.083s: "hello"' in envelope['word_schedule_content']
            assert manifest['word_timing']['clipped_word_count'] == 1
            assert abs((9/24 - 8/24) - 1/24) < 1e-15 and abs((10/24 - 8/24) - 2/24) < 1e-15
        dry_path = store.resolve_asset(dry.output.asset_id).path
        assert _raw_pixels(dry_path, 0, 8) == _raw_pixels(
            source_path, operation.window.source_range.start, operation.window.source_range.end
        )
        assert envelope["cpu_input"]["original_range"] == [
            operation.window.source_range.start, operation.window.source_range.end
        ]
        clip_receipts.append({
            "shot_id": shot, "extracted_cpu_sha256": manifest["source"]["proxy_sha256"],
            "dry_run_output_sha256": dry.output.sha256, "retained_replay_sha256": take.output.sha256,
            "original_source_start_frame": operation.window.source_range.start, "original_source_end_frame": operation.window.source_range.end,
            "decoded_frames": dry.output.frame_count, "decoded_pts": 0,
            "pad_left": operation.window.pad_left, "pad_right": operation.window.pad_right,
            "word_schedule_sha256": manifest["prompt"]["word_schedule_sha256"],
            "original_word_timing_canonical": canonical_words, "original_word_timing_sha256": word_sha,
            "effective_word_schedule": envelope['word_schedule_content'], "operation_fingerprint": operation.fingerprint,
            "protected_binding_sha256": binding.binding_sha256,
            "word_schedule_offset_frames": manifest["effective_overrides"]["word_offset_frames"], "h3_qualified": manifest["recipe"]["h3_qualified"],
        })
    assert all(item["h3_qualified"] is False and item["pad_left"] == item["pad_right"] == 0
               for item in clip_receipts)
    assert clip_receipts[1]["word_schedule_offset_frames"] == 8

    counts = _counts(database)
    assert counts == {
        "attempts": 5, "takes": 5, "qualified_replay_receipts": 2,
        "reviews": 2, "selection_events": 5, "edit_revisions": 1, "exports": 1,
    }
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        states = [row[0] for row in db.execute("SELECT state FROM attempts ORDER BY created_at")]
        ledger = {table: [dict(row) for row in db.execute(f'SELECT * FROM {table}')]
                  for table in ('attempts', 'attempt_events', 'provider_receipts', 'selection_events')}
        unchanged = db.execute(
            "SELECT output_sha256 FROM takes WHERE shot_id='shot-a' AND origin='dry_run'"
        ).fetchone()[0]
    assert states.count("completed") == 3
    assert states.count("provider_confirmed_cancelled") == 1
    assert states.count("reconcile_needed") == 1
    assert phase3["after"]["takes"][0]["output_sha256"] == unchanged
    assert restart_one_counts == restart_two_read_counts
    assert restart_three_read_counts == restart_two_post_counts

    public_receipt = {
        "fixture": {"source_sha256": scene.source.sha256, "source_frames": scene.source.frame_count, "shots": [item.id for item in scene.shots]},
        "serverRestarts": {"processes": 5, "database_sha256_after_initial_process": restart_one_hash,
                           "database_sha256_after_read_restart": restart_two_read_hash, "database_sha256_after_attempt_restart": restart_three_read_hash},
        "cpuClips": clip_receipts,
        "export": {"selected_sha256": checks["integrity"]["selected_sha256"], "final_sha256": final_hash,
                   "decoded_frames": 16, "decoded_pts": 0, "pixel_correspondence": checks["measurements"]["output_video_content"],
                   "source_check": {"frames": scene.source.frame_count, "hash": scene.source.sha256},
                   "render_check": [item for item in checks["measurements"]["decoded"] if item.get("kind") == "retained_replay"],
                   "pad_check": [{"shot_id": item["shot_id"], "padding_removed": item["padding_removed"]} for item in checks["authority"]],
                   "decode_check": checks["measurements"]["decoded"], "placement_check": checks["measurements"]["placement"],
                   "audio_comparison": checks["audio"]},
        "counts": counts,
        "teardown": teardown, "redacted_database_events": ledger,
        "browserPhases": {"source": "phase1.json", "preparedCpuAttempts": "phase2.json", "recoveryAndCompletedChallenge": "phase3.json", "queuedCancelReplayReviewExport": "phase4.json", "offlineUnknownAndRace": "safety.json"},
        "screenshots": sorted(path.name for path in evidence.glob('*.png')),
        "download": phase4["download"],
        "qualification": {"cpu_non_inference": True, "h3_qualified": False, "live_h3_provider_qualification": "OWNER_BLOCKED"},
    }
    assert "/Users/" not in json.dumps(public_receipt)
    (evidence / "journey-receipt.json").write_text(json.dumps(public_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

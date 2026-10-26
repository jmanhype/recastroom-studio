# Frontend follow-up evidence — status retry and keyboard controls

## Scope

This private, sanitized bundle supplements the earlier OJ-yf2c browser checkpoint. It contains 47 JPEG screenshots copied byte-for-byte from the status-retry capture, a condensed AX/keyboard event record, HTTP counts derived from the private request log, and a SHA-256 manifest with `sips` dimensions. Raw request logs, app data, credentials, and private absolute paths are not included.

## Measured follow-up

- Actual CUA keyboard traversal recorded the application controls, three native video containers (`source-preview`, `final-preview`, and `comparison-preview`), six native subcontrols after each container, the native menu items Download / Playback speed / Picture in Picture, reset, and both recovery buttons. AX identifies each focused native control. Host `focusVisible=false` on a shadow-DOM subcontrol is treated as expected shadow focus rather than immediately condemned.
- Representative visual inspection confirms the completed dry-run UI, the native menu, both health states, status recovery, and reset behavior. It does not clearly resolve a visible focus ring on every native subcontrol. AX plus screenshots therefore prove traversal, not an exhaustive visible-indicator audit or full WCAG pass.
- Job `85b97f14514e` made four status GET requests; all returned 200. There were zero HTTP 500 responses and exactly one intentional missing-job run 404. Across the 21 captured requests, the response counts were 12×200, 8×206, and 1×404.
- Removing the isolated source caused a real terminal ERROR. Restoring it and retrying traversed DOWNLOADING to COMPLETE. After the restored job produced the intentional run 404, keyboard Check job status again recovered to COMPLETE.
- On port 8895, a static HTTP server really returned `/api/health` 404. Replacing it with the actual dry-run API and pressing Enter recovered the connection state. Both QA tabs were explicitly closed; the IAB inventory retained only the original port-8893 tab. Ports 8894 and 8895 were stopped and the viewport override reset.
- The request UA declares `Chrome/155.0.0.0`, a reduced UA token. It does not establish the exact Chromium patch or full engine version. Codex app version `26.623.101652` comes from the earlier receipt, not a new measurement.

## Reduced-motion boundary

Two fresh native-Chrome rechecks of the actual `#result` animation were attempted; both CUA getApp calls failed ScreenCaptureKit audio/video capture with error `-3811`, so no new reduced-motion evidence was produced. The earlier preference/screenshot/body-CSS observation remains prior-turn evidence and is insufficient by itself because `body` is not the animated `#result` element. Full AC3 reduction proof, exact engine version, full WCAG conformance, score/release claims, capstone acceptance, and integrated full-test completion remain open.

## Process status

The parent reports that OJ-p8rd was independently accepted and merged to epic `7881cb0`, then live port 8893 restarted as PID 42810 with health and the original-job status returning 200. This packaging task performed no browser/network query, tracker transition, commit, merge, or push, so those live-process facts are recorded as parent-reported rather than independently revalidated here.

## Files

- `events.json` — sanitized event, environment, health, HTTP, recovery, and limits record.
- `screenshots/*.jpg` — unchanged copies of the 47 source screenshots.
- `SHA256SUMS.json` — SHA-256 and `sips` dimensions for every screenshot; hashes for the two other evidence files.

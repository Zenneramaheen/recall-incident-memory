# Live verification — 2026-09-28

Hindsight Cloud bank: `incident-demo-20260928-01`.

- Created the bank successfully using the locally configured key.
- Investigated the example alert before retaining any incident: zero evidence;
  returned the generic checklist with root cause unconfirmed.
- Retained `SYNTHETIC-001` synchronously.
- Investigated in a new Python process: returned four memory facts concerning
  pool saturation, the connection leak, rollback, and connection cleanup.
- Reflection described the temporarily helpful restart and the successful past
  fix, proposed checks for the current incident, cited sources, and explicitly
  identified the records as synthetic. It did not execute remediation.
- Three local unit tests passed after changes.

Example returned fact ID: `fe594013-adce-4bf6-8050-30426e6502ae`.

Fixed Python certificate loading by setting the certifi CA bundle before importing
the HTTP client; HTTPS verification remains enabled. Added client cleanup to avoid
unclosed-session warnings; the final live command exited successfully without them.

This is one synthetic smoke test, not a benchmark. The empty-memory checklist is
deterministic, not a controlled comparison against an LLM without memory. Retrieval
quality, every generated claim, cross-incident generalization, and recovery time
have not been evaluated. The synthetic incident omitted an event timestamp, so
Hindsight associated facts with the ingestion date; that date is not a real outage.

## Browser interface verification

The local interface at `http://127.0.0.1:8765` was tested against a separate fresh
Cloud bank, `incident-ui-43940340a67c`:

1. Created an empty bank through the interface.
2. Investigated the prefilled alert: zero facts and the generic checklist.
3. Saved the reviewed synthetic resolution through the form.
4. Reloaded the page, selected the same bank, and investigated again.
5. Received four facts including the failed restart, root cause, and successful
   rollback/cleanup fix. The response distinguished current hypotheses from the
   previous synthetic incident and requested review before remediation.

Seven local unit tests passed, including input validation and suppression of
private upstream error output. The desktop result was visually inspected. A
full-page screenshot is saved at `artifacts/recall-live-demo.png` (Git-ignored).
The server remains a local single-user demo; no public deployment was performed.

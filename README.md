# Incident Memory Copilot

A Python incident-memory prototype with an interactive checkout fault simulator.
Save verified incident resolutions in Hindsight, recall relevant experience, and
generate diagnostic recommendations. The simulator's buttons change only its own
state; the agent does not execute remediation or connect to production systems.

## Checkout lab — start here

Run `.venv/bin/python web_app.py` and open http://127.0.0.1:8765.
The green instruction card tells you what to do next.

1. **Place demo order**: the healthy shop accepts an order (no payment).
2. **First failure**, then **Place demo order**: checkout returns HTTP 503;
   the database pool is exhausted. **Ask the incident agent** analyzes the logs
   using Hindsight reflection, even with no prior memories.
3. Under **Try a fix yourself**, **Restart checkout** gives one successful order,
   then another order fails. **Repair connection cleanup** fixes the modeled bug.
4. Place an order to verify recovery, then **Save this lesson to Hindsight**.
5. **Same problem again**, place an order, ask the agent: it should retrieve the
   previous resolution and the unsuccessful restart.
6. **Looks similar. Isn’t.**, place an order, ask the agent: the HTTP 503 looks
   similar, but the database is healthy and the payment gateway is unreachable.
   The earlier connection patch does not fix this case. **Restore payment
   settings**, then place an order to verify recovery.

After each investigation, the **Why memory applies** card compares observable
signals from the current simulator with the recalled lesson. It labels the past
fix as applicable only when the database-pool and exception-path evidence match;
it labels the payment scenario as conflicting and tells the engineer not to reuse
the old connection fix. This card is deterministic and derived from the same
visible metrics and logs given to the agent.

The hidden scenario identifier is excluded from the agent input. The input
contains the visible simulator logs and metrics. Fault behavior is deterministic;
there is no real database pool or external payment integration. Checkout actions
produce real HTTP 200/503 responses from the local simulator endpoint. Model
answers are live and nondeterministic. The same reflection path handles first
and subsequent incidents; no canned bad answer is used in the lab's first round.

The tab keeps its session ID across reloads. Simulator state is in server memory
and resets on server restart. Hindsight lessons persist remotely. **New session**
starts a fresh simulator and memory-bank identity without deleting old banks.
Later chapters unlock only after a verified lesson has been saved successfully.

## Browser interface

After installing dependencies and saving your credentials in `.env`, run:

```sh
.venv/bin/python web_app.py
```

The original manual interface is at http://127.0.0.1:8765/console.

1. Choose **Fresh demo bank** for an empty bank, then **Investigate with memory**.
2. Open **Record resolution**, review the prefilled synthetic example, check the
   confirmation, and choose **Save resolution to memory**.
3. Return to **Investigate** and rerun the alert. Review retrieved evidence,
   recommendations, and the expandable list of sources used in reflection.

The original sample bank is preselected on each page load. Copy a newly created
bank name if you want to return to it after reloading. New banks are retained in
your Hindsight account; no existing bank is deleted by the interface.

This is a local development server, bound to loopback. Do not expose it publicly.
The server serves only explicitly allowed frontend files and sample data;
API credentials stay in Python. Model output is rendered as text with limited
Markdown formatting, never as raw HTML. Failed API calls show an error rather
than substitute mock results. This is a single-user demo, not a hosted service.

## Setup

Use Python 3.10 or newer and a running Hindsight server with its LLM configured.
See the [official setup guide](https://hindsight.vectorize.io/developer/api/quickstart).

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export HINDSIGHT_BASE_URL='http://localhost:8888'
# For a hosted instance, use its URL and set HINDSIGHT_API_KEY privately in your shell.
```

The application reads environment variables and the project's ignored .env file.
Existing shell variables take precedence over .env values.
Client dependencies are pinned to the installed versions. A live synthetic flow
was verified on 2026-09-28; see VALIDATION.md.

## Demonstrate persistent memory

Use a new bank name for a fresh comparison. The included incident and alert are
synthetic, not observations from a real production system.

```sh
python incident_memory.py --bank incident-demo-01 init
python incident_memory.py --bank incident-demo-01 investigate examples/alert.txt --service checkout --environment demo
python incident_memory.py --bank incident-demo-01 retain examples/resolved-incident.json
python incident_memory.py --bank incident-demo-01 investigate examples/alert.txt --service checkout --environment demo
```

The empty-bank output is an explicitly generic, deterministic checklist, not an
LLM baseline or evidence of measured improvement. After retaining, inspect the
returned fact IDs and the recommendation's supporting sources. Each invocation
is a fresh process; memory resides in Hindsight. Recall and reflection each search
memory, so their source lists may differ.

To record a new confirmed outcome, copy the incident JSON, give it a new ID, and
fill in the actual findings. Retaining the same ID replaces that document's memory;
use this deliberately to correct an existing record. Service and environment tags
restrict searches, but are not a substitute for authentication or tenant isolation.

## Verification and limits

```sh
python3 -m unittest discover -s tests -v
```

Tests use a fake client to verify empty-memory behavior, scoping, outcome retention,
and evidence presentation. They do not verify the hosted API or model quality.
Live retain/recall/reflect was verified using the configured Cloud endpoint and
the included synthetic incident. No real incident data was sent. Do not claim production
readiness, faster recovery, or a working live demo until measured and verified.

## Content submission plan

After live verification, capture real code and a before/after interaction for each
member's 1,200–1,500 word article, each member's LinkedIn post, and the team's
2–5 minute public YouTube demo. Keep articles and social posts free of the word
“hackathon”, including hashtags. Ground all claims in the implementation and
observed results. Follow the remaining publication/link requirements in the
[provided guide](https://docs.google.com/document/d/1Spy4cclvZtWFI_ynXLcSDGBSVqb_Zjp2M1ffXqWeOXU/edit).

API references: [Python client](https://hindsight.vectorize.io/sdks/python),
[retain](https://hindsight.vectorize.io/developer/api/retain),
[recall](https://hindsight.vectorize.io/developer/api/recall),
[reflect](https://hindsight.vectorize.io/developer/api/reflect).

## Presentation material

Use [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a 3-minute walkthrough and
[SLIDE_OUTLINE.md](SLIDE_OUTLINE.md) for six concise slides. Both are grounded
in the tested simulator behavior and state the prototype limits.

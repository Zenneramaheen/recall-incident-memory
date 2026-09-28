# How I Built Recall: An AI Agent That Learns From Past Incidents

When a production service fails, the immediate challenge is not only finding a fix. It is finding the right fix quickly, with enough evidence to trust it. Teams often face an especially frustrating version of this problem: an incident happens, a solution is found after a long investigation, and then months later a similar incident appears. The context is scattered across logs, chat messages, dashboards, and post-incident notes. The engineer on call must start from scratch or spend valuable time searching for a past answer.

I built **Recall**, an Incident Memory Copilot, to explore a better workflow. Recall stores lessons from engineer-confirmed incident resolutions and uses them during a later investigation. It does not simply retrieve an old note and claim that it is correct. It compares the past lesson with the current evidence and explains whether the old resolution applies.

The result is a small but important idea: experience should become usable memory. An engineer should be able to ask, “What do we know from last time?” and receive a useful, evidence-based answer.

## The problem: repeated investigations waste time

Incident response involves uncertainty. A checkout service returning HTTP 503 errors could be caused by a connection leak, a failing dependency, an overloaded database, a bad deployment, or a payment provider outage. The visible symptom alone is rarely enough to choose a safe remediation.

Many teams write incident notes after recovery. That is valuable, but a document by itself is passive. During a new outage, the on-call engineer still has to remember that the document exists, find it, decide whether it is relevant, and interpret it under pressure.

Recall turns the previous resolution into a memory that can be searched and evaluated in the context of a new incident. It is designed around two rules:

1. Store only lessons that an engineer has confirmed after recovery.
2. Never automatically execute a fix. The engineer remains responsible for approval and action.

## What I built

Recall includes a safe simulated checkout app called **Sunday Supply**. It has no real payments, customer details, or production systems. The shop interface lets a person place a demo order, while an engineer view shows the corresponding logs, metrics, and suggested next action.

The interface presents three short scenarios:

### 1. First failure: no previous memory

In the first scenario, the checkout fails with an HTTP 503 response. The engineer view shows that all 20 database connections are in use. The logs include an exception path that exits without releasing a database connection.

Recall has no earlier incident to retrieve. Instead of pretending it knows the answer, it says that there are zero recalled facts. It analyzes the current evidence and recommends sensible diagnostic steps: verify the recent release, inspect the exception-handling path, check the database sessions, and prepare a rollback plan. It also warns against simply increasing the connection limit, because that could hide a connection leak instead of resolving it.

This empty-memory behavior matters. A trustworthy assistant should be honest about what it does not know.

### 2. Same failure again: recall a verified solution

After the connection cleanup is repaired, a successful demo checkout verifies that the service has recovered. At that point, the engineer saves a lesson. The lesson records the symptoms, likely root cause, confirmed fix, and verification result.

When the same failure is simulated again, Recall retrieves the earlier lesson from Hindsight Cloud. It identifies that the database pool is exhausted again and that the current evidence matches the previous incident. The interface clearly shows why the memory applies: the same connection saturation and the same timeout pattern are present.

Recall can then recommend the previously verified connection-cleanup fix. It still presents the recommendation as guidance for the engineer to review, rather than silently changing a system.

### 3. A similar-looking failure with a different cause

The third scenario is the safety check. Checkout fails again, which could tempt an engineer to reuse the old database fix. But the visible evidence is different: the database pool is healthy, with only 4 of 20 connections in use, while the payment gateway is unreachable.

Recall searches the saved memory but rejects it as a match. It explains that the old database connection lesson conflicts with the current metrics and directs attention to the payment integration instead.

This is the behavior I wanted to demonstrate most. Good incident memory should not only help reuse useful knowledge. It should also prevent an old solution from being applied when the facts do not support it.

## How Hindsight Cloud is used

Hindsight Cloud provides the persistent memory layer for Recall. After an engineer confirms recovery, Recall stores the incident lesson using Hindsight. The stored information includes the service context, the observed symptoms, the root cause, the approved resolution, and the post-fix verification result.

During a later incident, Recall performs two kinds of work with that memory:

- **Recall:** find past incident lessons that may be relevant to the current issue.
- **Reflection:** combine the recalled lessons with the current logs and metrics to produce a structured investigation report.

The report distinguishes between recalled facts, current observations, recommended checks, and evidence still needed. This makes the agent’s reasoning more inspectable for the person using it.

The project deliberately keeps the Hindsight API key on the local backend. It is stored in a private environment file and is excluded from the public code repository. The browser never receives the key.

## Technology behind Recall

The project uses a simple, understandable stack:

- **Python** for the local backend, incident simulator, and Hindsight integration.
- **HTML, CSS, and JavaScript** for the interactive checkout and engineer interface.
- **Hindsight Cloud** for retaining, recalling, and reflecting on incident lessons.

The backend serves the local browser demo and controls the simulated scenarios. The frontend visualizes the checkout status, logs, metrics, agent report, memory comparison, and a small scorecard showing what the user has demonstrated.

The simulator is intentionally deterministic. It creates a database connection leak in one scenario and a payment gateway failure in another. That makes the demo repeatable while still showing the difference between a matching past incident and a conflicting one.

## Design choices for safety

Recall is not presented as an autonomous remediation system. Production changes can have serious consequences, so the engineer must remain in control. The agent can suggest a rollback, a configuration check, or a repair based on the evidence, but it does not perform those actions by itself.

I also avoided treating every past incident as a reliable answer. A memory is useful only when it matches the current context. The comparison view in Recall gives a clear result: applies, uncertain, or does not apply. This supports a safer form of assistance than plain keyword search.

Another important choice is verification. A lesson is only saved after the simulated checkout succeeds following the repair. This mirrors a practical incident workflow: record the resolution after confirming the service is actually healthy.

## What I learned

Building Recall made the difference between data storage and usable memory very clear. Storing a post-incident note is not enough. The value appears when an agent can retrieve the relevant experience at the right time, compare it with current evidence, explain its confidence, and know when not to reuse it.

There is also a human side to the idea. During an incident, people need clarity more than a long list of possibilities. Recall organizes the situation into a small investigation report: what happened before, what is happening now, what should be checked, and what cannot yet be assumed.

The current project is a prototype and a safe simulation. A future version could integrate with real observability systems, issue trackers, deployment history, and runbooks. It could also track confidence over time by learning from engineer feedback about which suggestions were useful.

For now, Recall demonstrates a focused workflow: break a checkout, investigate it, verify a repair, save the lesson, and see how persistent memory changes the next investigation.

## Explore the project

The complete source code is available here:

https://github.com/Zenneramaheen/recall-incident-memory

Hindsight Cloud is the memory system used by the project:

https://github.com/vectorize-io/hindsight

"""Deterministic checkout fault simulator. No payments or production systems."""
from datetime import datetime, timezone
from threading import RLock
import uuid


class CheckoutLab:
    def __init__(self):
        self.lock = RLock()
        self.bank = "checkout-lab-" + uuid.uuid4().hex[:12]
        self.bank_ready = False
        self.lessons_saved = 0
        self.round = 0
        self.chapter = None
        self.scorecard = {
            "first_investigated": False,
            "lesson_saved": False,
            "repeat_recalled": False,
            "different_rejected": False,
        }
        self.fault = "healthy"
        self.restart_grace = 0
        self.logs = []
        self.failed_attempts = []
        self.successful_fix = None
        self.verified = False
        self.failure_observed = False
        self.learned = False
        self.incident_id = None
        self.orders = 0
        self.last_checkout = None
        self.diagnosis = None
        self.opening_evidence = None

    def log(self, message):
        self.logs.append({"time": datetime.now(timezone.utc).strftime("%H:%M:%S"), "message": message})

    def metrics(self):
        leak = self.fault == "leak" and self.restart_grace == 0
        payment = self.fault == "payment"
        return {"database_connections": 20 if leak else 4, "database_capacity": 20,
                "payment_gateway": "unreachable" if payment else "reachable",
                "checkout": "degraded" if leak or payment else "healthy"}

    def snapshot(self):
        return {"bank": self.bank, "bank_ready": self.bank_ready, "lessons_saved": self.lessons_saved, "round": self.round,
                "chapter": self.chapter, "scorecard": self.scorecard.copy(),
                "metrics": self.metrics(), "logs": self.logs[-20:], "orders": self.orders,
                "last_checkout": self.last_checkout, "learned": self.learned,
                "can_learn": bool(self.successful_fix and self.verified and self.failure_observed),
                "incident_id": self.incident_id, "diagnosis": self.diagnosis,
                "failure_observed": self.failure_observed, "resolved": self.verified}

    def inject(self, scenario):
        if scenario not in ("first", "repeat", "different"):
            raise ValueError("Choose a valid scenario.")
        if scenario != "first" and not self.lessons_saved:
            raise ValueError("Save the first incident to memory before trying another scenario.")
        self.round += 1
        self.chapter = scenario
        self.fault = "payment" if scenario == "different" else "leak"
        self.restart_grace = 0
        self.logs = []
        self.failed_attempts = []
        self.successful_fix = None
        self.verified = self.failure_observed = self.learned = False
        self.diagnosis = self.last_checkout = self.opening_evidence = None
        self.incident_id = "LAB-" + uuid.uuid4().hex[:10]
        self.log("Synthetic deployment applied: checkout release " + str(self.round) + ".")
        return self.snapshot()

    def checkout(self):
        if self.fault == "leak" and self.restart_grace == 0:
            self.log("ERROR checkout HTTP 503: request timed out.")
            self.log("DB pool: 20/20 connections in use; acquire wait exceeded 5000ms.")
            self.log("Trace: exception handler exited without releasing its database connection.")
            status = 503
        elif self.fault == "payment":
            self.log("ERROR checkout HTTP 503: request timed out.")
            self.log("DB pool: 4/20 connections in use; query completed in 12ms.")
            self.log("Payment adapter: configured gateway sandbox-old.invalid could not resolve; payment request failed before authorization.")
            status = 503
        else:
            status = 200
            self.orders += 1
            self.log("OK checkout HTTP 200: demo order accepted; no payment collected.")
            if self.restart_grace:
                self.restart_grace -= 1
                self.log("Restart relief is temporary: leaking release is still deployed.")
            if self.successful_fix and self.fault == "healthy":
                self.verified = True
        self.last_checkout = {"status": status, "message": "Demo order placed. No money charged." if status == 200 else "Checkout timed out. Your demo order was not placed."}
        if status == 503:
            self.failure_observed = True
            if self.opening_evidence is None:
                self.opening_evidence = self.evidence()
        return status, self.snapshot()

    def action(self, action):
        if not self.failure_observed or self.verified:
            raise ValueError("First reproduce a checkout failure. Resolved incidents need no further fix.")
        if self.successful_fix:
            raise ValueError("A fix has been applied. Place an order to verify recovery before another action.")
        if action == "restart":
            if self.fault == "leak":
                self.restart_grace = 1
                outcome = "Restart cleared the pool temporarily, but the leaking release remains. One checkout may succeed before the failure returns."
            else:
                outcome = "Restart did not repair the unreachable payment gateway."
            self.failed_attempts.append(outcome)
        elif action == "connection-fix":
            if self.fault == "leak":
                self.fault = "healthy"
                self.restart_grace = 0
                self.successful_fix = "Patched the exception path to always release database connections."
                outcome = self.successful_fix + " Place a demo order to verify recovery."
            else:
                outcome = "Connection cleanup patch did not resolve the timeout: database was healthy; payment gateway remained unreachable."
                self.failed_attempts.append(outcome)
        elif action == "payment-fix":
            if self.fault == "payment":
                self.fault = "healthy"
                self.successful_fix = "Restored the simulator's valid payment gateway configuration."
                outcome = self.successful_fix + " Place a demo order to verify recovery."
            else:
                outcome = "Payment configuration change did not resolve database connection pool exhaustion."
                self.failed_attempts.append(outcome)
        else:
            raise ValueError("Unknown demo action.")
        self.log("ACTION: " + outcome)
        self.diagnosis = None
        return self.snapshot()

    def evidence(self):
        import json
        return ("Synthetic shopping checkout, service=checkout-lab, environment=simulation. "
                "Investigate using current evidence. Determine whether previous fixes apply, "
                "and explicitly identify evidence against reusing them. Do not assume a matching "
                "timeout means a matching cause. Current observations:\n" +
                json.dumps({"metrics": self.metrics(), "logs": self.logs[-15:]}, indent=2))

    def comparison(self, recalled_facts):
        """Explain memory applicability from visible evidence, never the hidden fault name."""
        if not recalled_facts:
            return {
                "status": "no-history",
                "title": "No past incident to compare",
                "summary": "The agent can analyze the current logs, but this is the first saved lesson for this checkout.",
                "matches": [], "conflicts": [],
                "decision": "Investigate the current evidence. Do not claim a past fix exists.",
            }
        metrics = self.metrics()
        log_text = " ".join(item["message"] for item in self.logs).lower()
        matches = ["Customer symptom: checkout returned HTTP 503."]
        conflicts = []
        if metrics["database_connections"] == metrics["database_capacity"]:
            matches.extend([
                "Database pool is exhausted: 20/20 connections are in use.",
                "Current log points to an exception path that did not release a connection.",
            ])
        else:
            conflicts.append("Database pool is healthy: 4/20 connections are in use, unlike the earlier pool-exhaustion incident.")
        if metrics["payment_gateway"] == "unreachable":
            conflicts.append("Payment gateway is unreachable now; the earlier database incident had a reachable gateway.")
        if "could not resolve" in log_text:
            conflicts.append("Current log identifies a gateway hostname that could not resolve, not a connection-release failure.")
        applicable = len(conflicts) == 0 and len(matches) >= 3
        return {
            "status": "applies" if applicable else "conflict",
            "title": "Past lesson applies" if applicable else "Past lesson does not apply",
            "summary": ("The key signals match the saved incident, but verify the deployed version before using its fix."
                        if applicable else "The same customer symptom has a different technical cause. Current evidence overrides the old fix."),
            "matches": matches, "conflicts": conflicts,
            "decision": ("Verify that the connection-cleanup patch is missing or reverted; do not rely on a restart."
                         if applicable else "Do not repair connection cleanup. Investigate and restore the payment gateway configuration."),
        }

    def record_investigation_result(self):
        if not self.diagnosis:
            return
        status = self.diagnosis.get("comparison", {}).get("status")
        if self.chapter == "first" and status == "no-history":
            self.scorecard["first_investigated"] = True
        elif self.chapter == "repeat" and status == "applies":
            self.scorecard["repeat_recalled"] = True
        elif self.chapter == "different" and status == "conflict":
            self.scorecard["different_rejected"] = True

    def resolution(self):
        if not (self.successful_fix and self.verified and self.failure_observed):
            raise ValueError("Apply a fix and place a successful demo order before saving the lesson.")
        cause = ("Database connections leaked on the exception path."
                 if "database" in self.successful_fix else "Payment gateway configuration pointed to an unreachable endpoint; database was healthy.")
        return {"id": self.incident_id, "service": "checkout-lab", "environment": "simulation",
                "symptoms": self.opening_evidence, "root_cause": cause,
                "successful_fix": self.successful_fix, "failed_attempts": self.failed_attempts,
                "verification": "A demo checkout returned HTTP 200 after the fix; current simulator checks show healthy dependencies.",
                "synthetic": True}

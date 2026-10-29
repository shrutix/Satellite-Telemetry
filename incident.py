"""Time-stamped incident log for working through an SOP step by step.
 
Plain Python with no Streamlit dependency, so it can be tested on its own.
 
The log enforces the discipline an SOP is meant to create:
  * steps are handled strictly in order, and each only once
  * a step can be skipped only with a written reason
  * an incident closes as "resolved" only after every step is handled, and as
    "handed_over" only after it has been escalated
  * nothing can be added once the incident is closed
Entries are append-only, and timestamps are timezone-aware UTC.
"""
 
import csv
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
 
OUTCOMES = ("resolved", "handed_over")
CSV_COLUMNS = ("timestamp", "incident", "operator", "event", "step", "detail", "note")
 
 
class IncidentError(RuntimeError):
    """An action was not allowed in the incident's current state."""
 
 
@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime
    operator: str
    event: str  # started, step_done, step_skipped, note, escalated, closed
    step: Optional[int]
    detail: str
    note: str = ""
 
 
def _utc_now():
    return datetime.now(timezone.utc)
 
 
class IncidentLog:
    def __init__(self, procedure, operator, trigger="", clock=None):
        """Open an incident for ``procedure`` (a ``sop.Procedure``).
 
        ``trigger`` describes what raised the alert. ``clock`` is a function
        returning the current time; it exists so tests can control time.
        """
        operator = (operator or "").strip()
        if not operator:
            raise IncidentError("An operator name is required.")
 
        self.procedure = procedure
        self.operator = operator
        self.escalated = False
        self.outcome = None
        self._clock = clock or _utc_now
        self._entries = []
        self._step_status = []  # "done" or "skipped", one per handled step
 
        detail = f"{procedure.id}: {procedure.title}"
        self._add("started", None, detail, trigger.strip())
 
    # -- state -- 
 
    @property
    def entries(self):
        return tuple(self._entries)
 
    @property
    def is_closed(self):
        return self.outcome is not None
 
    @property
    def next_step(self):
        """Number of the step to do next, or None when every step is handled."""
        n = len(self._step_status) + 1
        return n if n <= len(self.procedure.steps) else None
 
    @property
    def progress(self):
        """(steps handled, total steps)."""
        return len(self._step_status), len(self.procedure.steps)
 
    def step_status(self, step):
        """One of "done", "skipped", "current", or "pending"."""
        if not 1 <= step <= len(self.procedure.steps):
            raise IncidentError(f"Step {step} does not exist.")
        if step <= len(self._step_status):
            return self._step_status[step - 1]
        return "current" if step == self.next_step and not self.is_closed else "pending"
 
    # -- actions --
 
    def complete_step(self, step, note=""):
        self._require_step(step)
        self._step_status.append("done")
        self._add("step_done", step, self.procedure.steps[step - 1], note.strip())
 
    def skip_step(self, step, reason):
        reason = (reason or "").strip()
        if not reason:
            raise IncidentError("A reason is required to skip a step.")
        self._require_step(step)
        self._step_status.append("skipped")
        self._add("step_skipped", step, self.procedure.steps[step - 1], reason)
 
    def add_note(self, text):
        text = (text or "").strip()
        if not text:
            raise IncidentError("A note cannot be empty.")
        self._require_open()
        self._add("note", None, "", text)
 
    def escalate(self, note=""):
        self._require_open()
        self.escalated = True
        self._add("escalated", None, self.procedure.escalate_to, note.strip())
 
    def close(self, outcome, note=""):
        self._require_open()
        if outcome not in OUTCOMES:
            raise IncidentError(f"Outcome must be one of: {', '.join(OUTCOMES)}.")
        if outcome == "resolved" and self.next_step is not None:
            raise IncidentError(
                "Complete or skip every step before closing as resolved, "
                "or escalate and close as handed_over."
            )
        if outcome == "handed_over" and not self.escalated:
            raise IncidentError("Escalate the incident before closing it as handed over.")
        self.outcome = outcome
        self._add("closed", None, outcome, note.strip())
 
    # -- export -- 
 
    def to_rows(self):
        return [
            {
                "timestamp": e.timestamp.isoformat(timespec="seconds"),
                "incident": self.procedure.id,
                "operator": e.operator,
                "event": e.event,
                "step": "" if e.step is None else e.step,
                "detail": e.detail,
                "note": e.note,
            }
            for e in self._entries
        ]
 
    def to_csv(self):
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.to_rows())
        return buffer.getvalue()
 
    def to_markdown(self):
        """A readable incident report, suitable as a post-incident record."""
        done, total = self.progress
        lines = [
            f"# Incident report: {self.procedure.id}",
            "",
            "*Simulated, educational record. Not a real spacecraft incident.*",
            "",
            f"- **Procedure:** {self.procedure.title}",
            f"- **Severity:** {self.procedure.severity}",
            f"- **Operator:** {self.operator}",
            f"- **Escalation contact:** {self.procedure.escalate_to}",
            f"- **Status:** {self.outcome if self.is_closed else 'open'}",
            f"- **Steps handled:** {done} of {total}",
            "",
            "## Timeline",
            "",
        ]
        for e in self._entries:
            stamp = e.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            label = e.event.replace("_", " ")
            if e.step is not None:
                label += f" {e.step}"
            line = f"- **{stamp}** | {label}"
            if e.detail:
                line += f": {e.detail}"
            if e.note:
                line += f" (note: {e.note})"
            lines.append(line)
        return "\n".join(lines) + "\n"
 
    # -- internals -- 
 
    def _add(self, event, step, detail, note):
        self._entries.append(
            LogEntry(self._clock(), self.operator, event, step, detail, note)
        )
 
    def _require_open(self):
        if self.is_closed:
            raise IncidentError("This incident is closed.")
 
    def _require_step(self, step):
        self._require_open()
        expected = self.next_step
        if expected is None:
            raise IncidentError("Every step has already been handled.")
        if step != expected:
            raise IncidentError(f"Step {expected} must be handled next, not step {step}.")
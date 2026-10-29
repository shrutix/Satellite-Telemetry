"""Load and validate standard operating procedures (SOPs) from Markdown files.
 
File format
-----------
A procedure file starts with a front-matter block of ``key: value`` lines
between two ``---`` lines, followed by ``##`` sections::
 
    ---
    id: SOP-001
    title: Battery Voltage Below Limit
    channel: battery_voltage
    severity: High
    escalate_to: Power subsystem engineer on call
    ---
 
    ## Prerequisites      (optional, "-" bullet list)
    ## Steps              (required, numbered list 1, 2, 3...)
    ## Exit criteria      (required, "-" bullet list)
 
A list item may continue onto following lines if they are indented.
Files whose names start with an underscore (such as ``_TEMPLATE.md``) are
skipped by ``load_all``.
"""
 
import re
from dataclasses import dataclass
from pathlib import Path
 
from telemetry import CHANNELS
 
PROCEDURES_DIR = Path(__file__).resolve().parent / "procedures"
SEVERITIES = ("Low", "Medium", "High", "Critical")
REQUIRED_FIELDS = ("id", "title", "channel", "severity", "escalate_to")
ID_PATTERN = re.compile(r"^SOP-\d{3}$")
 
# Both patterns capture (label, text). Anchored at column 0 so that indented
# lines are treated as continuations of the previous item.
_NUMBERED = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")
_BULLET = re.compile(r"^([-*])\s+(.*\S)\s*$")
 
 
class ProcedureError(ValueError):
    """A procedure file is malformed or missing required content."""
 
 
@dataclass(frozen=True)
class Procedure:
    id: str
    title: str
    channel: str
    severity: str
    escalate_to: str
    steps: tuple
    exit_criteria: tuple
    prerequisites: tuple = ()
    source: str = ""
 
 
def _split_front_matter(text, source):
    lines = text.strip().splitlines()
    if not lines or lines[0].strip() != "---":
        raise ProcedureError(f"{source}: file must start with a '---' front-matter block")
 
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ProcedureError(f"{source}: front-matter block is not closed with '---'")
 
    meta = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ProcedureError(f"{source}: bad front-matter line: {line!r}")
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip()
    return meta, lines[end + 1:]
 
 
def _split_sections(body_lines):
    sections = {}
    current = None
    for line in body_lines:
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections
 
 
def _items(lines, pattern):
    """Return [(label, text), ...]; indented lines continue the previous item."""
    items = []
    for line in lines:
        match = pattern.match(line)
        if match:
            items.append([match.group(1), match.group(2).strip()])
        elif items and line.strip() and line[0].isspace():
            items[-1][1] += " " + line.strip()
    return [(label, text) for label, text in items]
 
 
def parse_procedure(text, source="<string>"):
    """Parse and validate one procedure from its Markdown text."""
    meta, body = _split_front_matter(text, source)
 
    missing = [name for name in REQUIRED_FIELDS if not meta.get(name)]
    if missing:
        raise ProcedureError(f"{source}: missing front-matter field(s): {', '.join(missing)}")
    if not ID_PATTERN.match(meta["id"]):
        raise ProcedureError(f"{source}: id {meta['id']!r} must look like SOP-001")
    if meta["channel"] not in CHANNELS:
        raise ProcedureError(
            f"{source}: unknown channel {meta['channel']!r} (expected one of {', '.join(CHANNELS)})"
        )
    if meta["severity"] not in SEVERITIES:
        raise ProcedureError(
            f"{source}: severity {meta['severity']!r} must be one of {', '.join(SEVERITIES)}"
        )
 
    sections = _split_sections(body)
 
    numbered = _items(sections.get("steps", []), _NUMBERED)
    if not numbered:
        raise ProcedureError(f"{source}: needs a '## Steps' section with numbered steps")
    numbers = [int(label) for label, _ in numbered]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ProcedureError(f"{source}: steps must be numbered 1..{len(numbers)} in order, got {numbers}")
 
    exit_criteria = _items(sections.get("exit criteria", []), _BULLET)
    if not exit_criteria:
        raise ProcedureError(f"{source}: needs an '## Exit criteria' section with bullet items")
 
    prerequisites = _items(sections.get("prerequisites", []), _BULLET)
 
    return Procedure(
        id=meta["id"],
        title=meta["title"],
        channel=meta["channel"],
        severity=meta["severity"],
        escalate_to=meta["escalate_to"],
        steps=tuple(text for _, text in numbered),
        exit_criteria=tuple(text for _, text in exit_criteria),
        prerequisites=tuple(text for _, text in prerequisites),
        source=source,
    )
 
 
def load_procedure(path):
    """Read and validate a single procedure file."""
    path = Path(path)
    return parse_procedure(path.read_text(encoding="utf-8"), source=path.name)
 
 
def load_all(directory=None):
    """Load every procedure in a folder, keyed by id.
 
    Skips files whose names start with an underscore (e.g. the template).
    """
    directory = PROCEDURES_DIR if directory is None else Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Procedures folder not found: {directory}")
 
    procedures = {}
    for path in sorted(directory.glob("*.md")):
        if path.name.startswith("_"):
            continue
        procedure = load_procedure(path)
        if procedure.id in procedures:
            raise ProcedureError(
                f"Duplicate id {procedure.id} in {path.name} and {procedures[procedure.id].source}"
            )
        procedures[procedure.id] = procedure
    return procedures
 
 
def for_channel(procedures, channel):
    """Procedures that apply to a telemetry channel, sorted by id."""
    return sorted((p for p in procedures.values() if p.channel == channel), key=lambda p: p.id)
import pytest
 
from sop import (
    PROCEDURES_DIR,
    REQUIRED_FIELDS,
    SEVERITIES,
    ProcedureError,
    for_channel,
    load_all,
    load_procedure,
    parse_procedure,
)
from telemetry import CHANNELS
 
BODY = """## Prerequisites
- Display is live
 
## Steps
1. First step.
2. Second step that is long
   and continues here.
3. Third step.
 
## Exit criteria
- Back in limits for 10 minutes
"""
 
 
def make_text(front=None, body=None):
    meta = {
        "id": "SOP-042",
        "title": "Test procedure",
        "channel": "temperature_c",
        "severity": "Medium",
        "escalate_to": "Thermal engineer",
    }
    meta.update(front or {})
    front_lines = "\n".join(f"{k}: {v}" for k, v in meta.items() if v is not None)
    return f"---\n{front_lines}\n---\n\n{BODY if body is None else body}"
 
 
# --- parsing -----------------------------------------------------------------
 
def test_parses_a_valid_procedure():
    p = parse_procedure(make_text())
    assert (p.id, p.channel, p.severity) == ("SOP-042", "temperature_c", "Medium")
    assert p.escalate_to == "Thermal engineer"
    assert p.prerequisites == ("Display is live",)
    assert p.exit_criteria == ("Back in limits for 10 minutes",)
    assert len(p.steps) == 3
 
 
def test_indented_lines_continue_the_previous_step():
    p = parse_procedure(make_text())
    assert p.steps[1] == "Second step that is long and continues here."
 
 
def test_prerequisites_are_optional():
    body = "## Steps\n1. Do it.\n\n## Exit criteria\n- Done\n"
    assert parse_procedure(make_text(body=body)).prerequisites == ()
 
 
@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_missing_front_matter_field_raises(field):
    with pytest.raises(ProcedureError, match=field):
        parse_procedure(make_text(front={field: None}))
 
 
@pytest.mark.parametrize("bad_id", ["SOP-1", "sop-001", "SOP-0001", "PROC-001"])
def test_bad_id_format_raises(bad_id):
    with pytest.raises(ProcedureError, match="id"):
        parse_procedure(make_text(front={"id": bad_id}))
 
 
def test_unknown_channel_raises():
    with pytest.raises(ProcedureError, match="channel"):
        parse_procedure(make_text(front={"channel": "warp_core_temp"}))
 
 
def test_unknown_severity_raises():
    with pytest.raises(ProcedureError, match="severity"):
        parse_procedure(make_text(front={"severity": "Urgent"}))
 
 
def test_missing_front_matter_raises():
    with pytest.raises(ProcedureError, match="front-matter"):
        parse_procedure(BODY)
 
 
def test_unclosed_front_matter_raises():
    with pytest.raises(ProcedureError, match="not closed"):
        parse_procedure("---\nid: SOP-001\n" + BODY)
 
 
def test_missing_steps_raises():
    with pytest.raises(ProcedureError, match="Steps"):
        parse_procedure(make_text(body="## Exit criteria\n- Done\n"))
 
 
def test_missing_exit_criteria_raises():
    with pytest.raises(ProcedureError, match="Exit criteria"):
        parse_procedure(make_text(body="## Steps\n1. Do it.\n"))
 
 
def test_steps_must_be_numbered_in_order():
    body = "## Steps\n1. First.\n3. Skipped two.\n\n## Exit criteria\n- Done\n"
    with pytest.raises(ProcedureError, match="numbered"):
        parse_procedure(make_text(body=body))
 
 
# --- loading from disk -------------------------------------------------------
 
def write_sop(folder, name, **front):
    (folder / name).write_text(make_text(front=front), encoding="utf-8")
 
 
def test_load_procedure_reads_a_file(tmp_path):
    write_sop(tmp_path, "thermal.md")
    p = load_procedure(tmp_path / "thermal.md")
    assert p.id == "SOP-042" and p.source == "thermal.md"
 
 
def test_load_all_skips_underscore_files(tmp_path):
    write_sop(tmp_path, "thermal.md")
    (tmp_path / "_draft.md").write_text("this is not a valid procedure", encoding="utf-8")
    assert list(load_all(tmp_path)) == ["SOP-042"]
 
 
def test_duplicate_ids_raise(tmp_path):
    write_sop(tmp_path, "a.md")
    write_sop(tmp_path, "b.md")
    with pytest.raises(ProcedureError, match="Duplicate"):
        load_all(tmp_path)
 
 
def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Procedures folder"):
        load_all(tmp_path / "nope")
 
 
def test_for_channel_filters_and_sorts(tmp_path):
    write_sop(tmp_path, "b.md", id="SOP-002", channel="temperature_c")
    write_sop(tmp_path, "a.md", id="SOP-001", channel="temperature_c")
    write_sop(tmp_path, "c.md", id="SOP-003", channel="battery_voltage")
    found = for_channel(load_all(tmp_path), "temperature_c")
    assert [p.id for p in found] == ["SOP-001", "SOP-002"]
 
 
# ---  procedures actually shipped in this ----------------------------
 
def test_shipped_procedures_load_and_are_valid():
    procedures = load_all()
    assert procedures, "expected at least one procedure in procedures/"
    for p in procedures.values():
        assert p.severity in SEVERITIES
        assert p.channel in CHANNELS
        assert p.escalate_to
 
 
def test_template_exists_and_is_not_loaded_as_a_procedure():
    assert (PROCEDURES_DIR / "_TEMPLATE.md").exists()
    assert all(p.source != "_TEMPLATE.md" for p in load_all().values())
 
 
def test_battery_channel_has_a_procedure():
    assert for_channel(load_all(), "battery_voltage")
 
 
@pytest.mark.parametrize("channel", CHANNELS)
def test_every_channel_has_a_procedure(channel):
    assert for_channel(load_all(), channel), f"no SOP covers {channel}"
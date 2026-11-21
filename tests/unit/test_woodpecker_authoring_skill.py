from pathlib import Path

SKILL = (
    Path(__file__).parent.parent.parent
    / ".agents"
    / "skills"
    / "woodpecker-authoring-pipelines.md"
)


def test_skill_has_probe_technique_and_exec_guardrail():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\nname: woodpecker-authoring-pipelines\n")
    assert "probe" in text and "--pipeline-event push" in text


def test_skill_credits_source_and_is_not_a_generic_ci_skill():
    text = SKILL.read_text(encoding="utf-8")
    assert "pickled-claude-plugins" in text and "MIT" in text
    assert not SKILL.with_name("ci-hardening.md").exists()

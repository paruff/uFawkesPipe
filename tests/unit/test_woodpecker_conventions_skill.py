from pathlib import Path

SKILL = (
    Path(__file__).parent.parent.parent
    / ".agents"
    / "skills"
    / "woodpecker-pipeline-conventions.md"
)


def test_skill_has_frontmatter_and_core_rules():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\nname: woodpecker-pipeline-conventions\n")
    for rule in ("latest", "from_secret", "/bin/sh", "Ask the owner first"):
        assert rule in text


def test_skill_is_not_duplicated_under_claude_dir():
    assert not (SKILL.parents[3] / ".claude" / "skills" / SKILL.name).exists()

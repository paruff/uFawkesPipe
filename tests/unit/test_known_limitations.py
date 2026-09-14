import pytest
import re
from pathlib import Path


class TestKnownLimitations:
    """Tests for KNOWN_LIMITATIONS.md validation."""

    @pytest.fixture
    def limitations_file(self):
        return Path(__file__).parent.parent.parent / "docs" / "KNOWN_LIMITATIONS.md"

    @pytest.fixture
    def limitations_content(self, limitations_file):
        return limitations_file.read_text(encoding="utf-8")

    def test_all_limitations_are_resolved(self, limitations_content):
        """All limitation entries must be marked RESOLVED in the Impact or Mitigation column."""
        tables = self._extract_tables(limitations_content)

        unresolved = []
        for table in tables:
            if not self._is_limitation_table(table):
                continue
            for row in table["rows"]:
                limitation_id = row.get("#", "").strip()
                if not limitation_id or limitation_id == "#":
                    continue

                impact = row.get("Impact", "").strip()
                mitigation = row.get("Mitigation", "").strip()

                is_resolved = impact.startswith("**RESOLVED:**") or mitigation.startswith("**RESOLVED:**")

                if not is_resolved:
                    unresolved.append(limitation_id)

        assert not unresolved, f"Unresolved limitations (missing **RESOLVED:** in Impact or Mitigation): {unresolved}"

    def test_no_strikethrough_without_resolved(self, limitations_content):
        """Strikethrough (~~) items should be marked RESOLVED in the Impact or Mitigation column."""
        tables = self._extract_tables(limitations_content)

        issues = []
        for table in tables:
            if not self._is_limitation_table(table):
                continue
            for row in table["rows"]:
                limitation_text = row.get("Limitation", "").strip()
                impact = row.get("Impact", "").strip()
                mitigation = row.get("Mitigation", "").strip()

                if limitation_text.startswith("~~"):
                    if not impact.startswith("**RESOLVED:**") and not mitigation.startswith("**RESOLVED:**"):
                        issues.append(f"Strikethrough without RESOLVED: {limitation_text[:50]}")

        assert not issues, f"Strikethrough items missing RESOLVED: {issues}"

    def test_all_limitations_have_ids(self, limitations_content):
        """All limitation rows must have an ID (L-XXX format)."""
        tables = self._extract_tables(limitations_content)

        missing_ids = []
        for table in tables:
            if not self._is_limitation_table(table):
                continue
            for row in table["rows"]:
                limitation_id = row.get("#", "").strip()
                if not limitation_id or limitation_id == "#":
                    continue

                if not re.match(r"^L-\d{3}$", limitation_id):
                    missing_ids.append(limitation_id)

        assert not missing_ids, f"Limitations with invalid IDs: {missing_ids}"

    def _extract_tables(self, content):
        """Extract markdown tables from content."""
        tables = []
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("|") and "|" in line:
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                if len(table_lines) >= 3:
                    tables.append(self._parse_table(table_lines))
            else:
                i += 1
        return tables

    def _parse_table(self, lines):
        """Parse markdown table into headers and rows."""
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
        return {"headers": headers, "rows": rows}

    def _is_limitation_table(self, table):
        """Check if table is a limitation table (has #, Limitation, Impact, Mitigation columns)."""
        return all(col in table["headers"] for col in ["#", "Limitation", "Impact", "Mitigation"])
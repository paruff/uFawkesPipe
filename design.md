# PIPE-002 — Design: Trivy Image Tag Policy Exception

## 1. Impacted Components

| Component | File | Change |
|---|---|---|
| Contribution Policy | `CONTRIBUTING.md` | Add formal exception block for scanner images |
| Security Unit Tests | `tests/unit/test_woodpecker_yml.py` | Add explanatory comments on `test_uses_trivy_latest` methods |

---

## 2. Design Approach

### 2.1 Policy: Formal Exception Block

**Where:** `CONTRIBUTING.md`, after the "What We Don't Accept" section, before "Running Tests".

**Rationale:** Vulnerability scanner images (like `aquasec/trivy:latest`) must remain unpinned because:
- Vulnerability definitions (CVE database) are bundled into the scanner image.
- Using a pinned version would scan against a stale vulnerability database, rendering scans ineffective for newly discovered CVEs.
- Pinning would require constant automated updates (e.g., Renovate/Dependabot) and rebuilds of the CI pipeline — introducing operational complexity and risk.

**Text to add:**

```markdown
### Exception: Vulnerability Scanner Images

The following images are exempted from the no-`:latest` rule because they must
contain the most current vulnerability definitions:

- `aquasec/trivy:latest`
- (placeholder for future scanner images that share the same operational constraint)

**Operational justification:**

Vulnerability scanners bundle CVE databases inside their container image. Pinning
a specific tag would freeze the scanner to a stale vulnerability database, missing
CVEs discovered after the pinned version. Updating scanner images automatically
requires Renovate/Dependabot infrastructure that is out of scope for this repo.

All other images (Woodpecker, SonarQube, Portainer, DefectDojo, buildpack tools,
Python base images) remain pinned per the general rule.
```

### 2.2 Test Comments

**Where:** `tests/unit/test_woodpecker_yml.py`, methods `test_uses_trivy_latest` in both `TestVulnScanFsStep` and `TestVulnScanImageStep`.

**What:** Add a comment above or at the top of each test method body explaining:

```python
# Trivy uses :latest intentionally — scanner images require current
# CVE databases bundled in the image. This is a documented exception,
# not a policy violation. See CONTRIBUTING.md §"Exception: Vulnerability
# Scanner Images" and docs/ARCHITECTURE.md §"Image pinning policy".
```

**Bug:** No functional changes. No image pinning. Comments only.

---

## 3. Anti-Goals

- Do not rename or move test methods.
- Do not change the `:latest` tag in `.woodpecker.yml`.
- Do not introduce new tests.
- Do not modify any pipeline steps.

"""Smoke test: a Trivy report imports into DefectDojo and the API reports its findings.

Needs `make up-security` plus DOJO_API_TOKEN (the initializer pins the admin token to it).
"""

import json
import os
import urllib.error
import urllib.request
import uuid

import pytest

BASE = os.environ.get("DOJO_URL", "http://localhost:8080")
TOKEN = os.environ.get("DOJO_API_TOKEN", "")

TRIVY_REPORT = {
    "SchemaVersion": 2,
    "ArtifactName": "smoke",
    "Results": [
        {
            "Target": "requirements.txt",
            "Class": "lang-pkgs",
            "Type": "pip",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2099-0001",
                    "PkgName": "demo",
                    "InstalledVersion": "1.0",
                    "FixedVersion": "1.1",
                    "Severity": "HIGH",
                    "Title": "smoke finding",
                    "Description": "synthetic",
                }
            ],
        }
    ],
}


def _call(path, data=None, headers=None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Authorization": f"Token {TOKEN}", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed local URL
        return resp.status, json.load(resp)


@pytest.mark.smoke
def test_trivy_import_creates_finding():
    if not TOKEN:
        pytest.skip("DOJO_API_TOKEN not set")
    try:
        _call("/api/v2/user_profile/")
    except (urllib.error.URLError, OSError):
        pytest.skip("DefectDojo not reachable (make up-security)")

    product = f"smoke-{uuid.uuid4().hex[:8]}"
    boundary = uuid.uuid4().hex
    fields = {
        "scan_type": "Trivy Scan",
        "product_name": product,
        "engagement_name": "smoke",
        "product_type_name": "Research and Development",
        "auto_create_context": "true",
        "active": "true",
    }
    body = b"".join(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, v in fields.items()
    )
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        'filename="trivy.json"\r\nContent-Type: application/json\r\n\r\n'
    ).encode() + json.dumps(TRIVY_REPORT).encode() + f"\r\n--{boundary}--\r\n".encode()

    status, _ = _call(
        "/api/v2/import-scan/",
        body,
        {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    assert status == 201

    _, found = _call(f"/api/v2/findings/?test__engagement__product__name={product}")
    assert found["count"] == 1

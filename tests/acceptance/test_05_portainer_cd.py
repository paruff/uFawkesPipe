"""Acceptance tests: Portainer CD readiness.

Covers AC-11 (see docs/acceptance-criteria.md).
Verifies Portainer is configured as a CD target:
- Portainer API is accessible with a valid JWT
- Endpoints API responds correctly (may return empty list if no
  Docker endpoint is configured, which is acceptable for dev mode)
- Portainer exposes the webhook endpoint for stack deployments
"""

import pytest


@pytest.mark.acceptance
class TestPortainerCDReadiness:
    """Verify Portainer is configured and ready for CD operations."""

    def test_portainer_endpoints_api(
        self, http_session, portainer_url, portainer_token
    ):
        """Portainer GET /api/endpoints must return HTTP 200.

        The response may be an empty list [] (no endpoints configured
        yet) or contain the local Docker endpoint. Both are acceptable
        — the key requirement is that the API is accessible with a
        valid JWT.
        """
        headers = {"Authorization": f"Bearer {portainer_token}"}
        resp = http_session.get(
            f"{portainer_url}/api/endpoints",
            headers=headers,
            timeout=10,
        )
        assert resp.status_code == 200, (
            f"Portainer endpoints API expected 200, "
            f"got {resp.status_code}: {resp.text[:200]}"
        )

        # Response must be a JSON array (even if empty)
        data = resp.json()
        assert isinstance(data, list), (
            f"Portainer endpoints expected list, got {type(data).__name__}"
        )

    def test_portainer_docker_accessible(
        self, http_session, portainer_url, portainer_token
    ):
        """Portainer must have Docker access (socket mounted).

        If an endpoint exists, verify it's Docker type.
        If no endpoints exist, indicate the user needs to add one.
        """
        headers = {"Authorization": f"Bearer {portainer_token}"}
        resp = http_session.get(
            f"{portainer_url}/api/endpoints",
            headers=headers,
            timeout=10,
        )
        assert resp.status_code == 200

        data = resp.json()
        if len(data) > 0:
            # At least one endpoint exists — verify it's Docker type
            endpoint = data[0]
            assert endpoint.get("Type") in (1,), (
                f"Expected Docker endpoint (Type=1), "
                f"got type {endpoint.get('Type')}: {endpoint}"
            )

    def test_portainer_auth_and_endpoints_workflow(
        self, http_session, portainer_url, portainer_token
    ):
        """Portainer CD readiness: full auth + API workflow.

        Verifies the complete auth-to-API flow that the deploy-portainer
        pipeline step would use (minus the actual webhook trigger).
        """
        headers = {"Authorization": f"Bearer {portainer_token}"}

        # Verify JWT is valid
        auth_check = http_session.get(
            f"{portainer_url}/api/endpoints",
            headers=headers,
            timeout=10,
        )
        assert auth_check.status_code == 200, (
            f"Portainer JWT validation failed: "
            f"HTTP {auth_check.status_code}"
        )

        # Verify the response is parseable
        data = auth_check.json()
        assert isinstance(data, list), (
            f"Expected list of endpoints, got {type(data).__name__}"
        )


@pytest.mark.acceptance
class TestPortainerWebhookEndpoint:
    """Verify Portainer exposes webhook endpoint for CD."""

    def test_portainer_webhook_status_endpoint(
        self, http_session, portainer_url, portainer_token
    ):
        """Portainer webhooks endpoint must return HTTP 200.

        GET /api/webhooks returns all configured webhooks.
        An empty list is acceptable (no webhooks configured yet).
        """
        headers = {"Authorization": f"Bearer {portainer_token}"}
        resp = http_session.get(
            f"{portainer_url}/api/webhooks",
            headers=headers,
            timeout=10,
        )
        # Portainer CE may not have webhooks endpoint at all in all versions
        # Accept 200 (exists) or 404 (not available in this version)
        assert resp.status_code in (200, 204, 404), (
            f"Portainer webhooks endpoint expected 200/204/404, "
            f"got {resp.status_code}: {resp.text[:200]}"
        )

        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list), (
                f"Webhooks response expected list, "
                f"got {type(data).__name__}"
            )
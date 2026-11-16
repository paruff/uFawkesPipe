"""The DORA event schemas here must agree with uFawkesObs's, the enforcing side.

Reads uFawkesObs's dora/events/*.schema.json at the release pinned in
contracts/dora-events/OBS_RELEASE and compares event types, required fields and
property names with the mirror. Offline runs skip; CI (CI=true) fails instead.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

MIRROR = Path(__file__).parent.parent.parent / "contracts" / "dora-events"
RAW = "https://raw.githubusercontent.com/paruff/uFawkesObs/{release}/dora/events/{name}"


def github_headers():
    # Unauthenticated api.github.com allows 60 requests an hour per IP, which shared CI runners exhaust.
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return headers


def shape(schema):
    return {
        "required": sorted(schema.get("required", [])),
        "properties": sorted(schema.get("properties", {})),
    }


def fetch(release, name):
    try:
        with urllib.request.urlopen(
            RAW.format(release=release, name=name), timeout=20
        ) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError) as e:
        if os.environ.get("CI"):
            pytest.fail(f"cannot read uFawkesObs {release} {name}: {e}")
        pytest.skip(f"offline: {e}")


@pytest.fixture(scope="module")
def release():
    return (MIRROR / "OBS_RELEASE").read_text().strip()


@pytest.mark.parametrize(
    "path", sorted(MIRROR.glob("*.schema.json")), ids=lambda p: p.name
)
def test_mirror_schema_matches_obs(path, release):
    assert shape(json.loads(path.read_text())) == shape(fetch(release, path.name)), (
        f"{path.name} differs from uFawkesObs {release}; port the change (docs/dora-contract.md)"
    )


def test_every_obs_event_type_is_mirrored(release):
    listing = urllib.request.Request(
        f"https://api.github.com/repos/paruff/uFawkesObs/contents/dora/events?ref={release}",
        headers=github_headers(),
    )
    try:
        with urllib.request.urlopen(listing, timeout=20) as r:
            theirs = {
                e["name"] for e in json.load(r) if e["name"].endswith(".schema.json")
            }
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            # Rate limit, not drift: the per-schema cases above read raw.githubusercontent.com, which has none.
            pytest.skip(
                f"api.github.com rate limit ({e.code}); new Obs event types not checked this run"
            )
        pytest.fail(f"cannot list uFawkesObs {release}: {e}")
    except (urllib.error.URLError, TimeoutError) as e:
        if os.environ.get("CI"):
            pytest.fail(f"cannot list uFawkesObs {release}: {e}")
        pytest.skip(f"offline: {e}")
    assert theirs == {p.name for p in MIRROR.glob("*.schema.json")}

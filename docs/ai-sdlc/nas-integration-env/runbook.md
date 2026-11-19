# Runbook: deploy uFawkesObs and uFawkesPipe on the NAS

Companion to [`plan.md`](plan.md) (phases 1 to 3). Backups are a backlog item by
the owner's decision (2026-11-18, paruff/eshelfstack#16): nothing here touches an
existing stack's data, but the Arcane migration must not start before that backlog
item is done. Facts below come from the compose files and the eshelfstack change
records; each "check" is for you to run, since nothing has been run on the NAS.

## NAS facts, read over SSH on 2026-11-18 (read-only)

| Item | Value | Consequence |
|---|---|---|
| RAM | 19.8 GB total, 15.6 GB available, 3.8 GB used, 14 GB swap | Obs `core` fits |
| Disk | `/volume1` 32 TB, 12 TB used, 20 TB free | No constraint |
| CPU / load | 4 cores, load average 0.4 | Headroom |
| Docker / Compose | Docker 24.0.2, Compose **v2.20.1** (`/usr/local/bin/docker`; not on the non-interactive SSH `PATH`) | `!override` and `!reset` (need 2.24) don't work; see below |
| Ports already listening on all interfaces | 3000, 5001, 8000, 9000, 9443 | Grafana (3000), `telemetry-generator` (5001), Woodpecker (8000, 9000) and Pipe's Portainer (9443) all collide |

## 0. Preflight (read-only)

```
free -m                       # DS920+ ships with 4 GB RAM; Obs's core profile sets limits above that
df -h /volume1                # room for Prometheus, Loki and Tempo data
/usr/local/bin/docker compose version   # the NAS has v2.20.1
sudo netstat -tlnp | grep -E ':(3000|8000|8088|9000|9090|9443)\b'
```

## What will collide, and the fix

| Collision | Cause | Fix |
|---|---|---|
| Ports 8000, 9000, 9443 | The existing Portainer CE publishes them; Pipe's `woodpecker-server` (8000, 9000) and `portainer` (9443) want the same | Host ports must become configurable (below). Skip Pipe's own Portainer: it would collide on 9443 and the NAS already runs one |
| Port 5001 | Obs's `telemetry-generator` publishes 5001, which is DSM's default HTTPS port | Don't start it: it is a demo generator |
| Port 3000 | Grafana, on all interfaces; something already listens on 3000 | Make Grafana's host port configurable in Obs, or stop the other service |
| Memory | Obs `core` limits are Tempo 4 GB, Loki 2 GB, Prometheus 2 GB, Grafana and others on top | The NAS now has 19.8 GB with 15.6 GB available: fits. Still watch `docker stats` the first day |
| `dora-api` unreachable | Obs binds it to `127.0.0.1:8088`, so a container on another network can't reach it | Join the runner and Woodpecker to Obs's network `observability-lab` and use `http://dora-api:8088` |

**The override approach doesn't work on this NAS.** A compose override file can't drop
a port the base file publishes without `!override`, and Compose v2.20.1 predates it. Two
ways out, both needing the owner's approval because they touch compose structure:

1. **Recommended:** make the host ports in `compose.yaml` configurable, defaulting to
   today's values, e.g. `"${WOODPECKER_UI_PORT:-8000}:8000"`, and drop the host
   publication of 9000 (the agent reaches the server over the compose network). Same for
   Obs's Grafana. Nothing changes for anyone who sets nothing.
2. Upgrade Container Manager to a Compose 2.24 or later, then use an override with
   `ports: !override`.

Until one of those lands, don't start Pipe's `woodpecker-server` or `portainer` on the
NAS. Set `WOODPECKER_HOST=http://<nas-ip>:<chosen port>` in `.env` once the port is chosen.

## 1. uFawkesObs first

```
cd uFawkesObs && docker compose --profile core up -d
docker network inspect observability-lab > /dev/null && echo network-ok
docker exec $(docker ps -qf name=dora-api) python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8088/health', timeout=5).status)"   # the image has no wget or curl
```
Expected: the network exists and the health call prints 200. Pin versions as the repo does; no `latest`.

## 2. uFawkesPipe in suite mode

```
cd uFawkesPipe && cp .env.example .env     # fill the secrets; never commit .env
docker compose -f compose.yaml -f compose.suite.yaml up -d   # after the port change above
```
Suite mode currently depends on the deprecated uFawkesRes for Postgres and Traefik
(AGENTS.md section 10, #97). If that blocks you, run standalone mode
(`-f compose.yaml`) and give Woodpecker the Obs network by hand.
Woodpecker's webhook needs GitHub to reach it; on a LAN-only NAS that won't happen, so
trigger pipelines from the Woodpecker UI or `woodpecker-cli` until a tunnel is chosen.

## 3. The runner

Merge the socket-proxy change (uFawkesPipe#251) first. Then, in `runner/.env`:
`RUNNER_REPO_URL=https://github.com/paruff/python-fawkes-path`, a fresh `RUNNER_TOKEN`,
`DOCKER_SOCKET=/var/run/docker.sock`. Attach the runner to `observability-lab`
(an override that declares it `external: true`) so the job can reach `dora-api`.
Then `docker compose -f runner/compose.yaml --env-file runner/.env up -d` and check
that the runner shows online under the repo's Settings, Actions, Runners.

## 4. The real run (closes #220)

In `python-fawkes-path`, set the secret `DORA_INGESTION_URL=http://dora-api:8088`
(add `DORA_API_KEY` if Obs requires one), then dispatch the "DORA event (test
environment)" workflow twice: once as is, once with `simulate_failure`. Expected: two
events accepted with 201 in `dora-api`'s log, statuses `success` and `failed`, and the
successful one carrying `first_commit_at`. Record both in `docs/ci-runner-image/verification-log.md`.

## What the first deploy found (2026-11-18)

Corrections to the steps above, from running them on the NAS.

- **Obs was already there.** `~/uFawkesObs` (the checkout the old containers came from)
  held a stale commit and seven exited core containers, started from two untracked files,
  `compose.drill.yaml` (an old full copy; unused) and `compose.drill-user.yaml` (a 242-byte
  override that sets `user: "1026:100"`). Update that checkout to `main` and start with
  `-f compose.yaml -f compose.drill-user.yaml --profile core --profile dora`.
- **`dora-api` needs the same user override.** Its container name is `ufawkesdora-ingestion`
  and it bind-mounts `dora/ingestion` and `dora/events` from the home folder, which has
  Synology ACLs. As uid 999 it crash-looped with `PermissionError: /app/ingestion/__init__.py`;
  adding `dora-api: user: "1026:100"` to `compose.drill-user.yaml` fixed it. The DORA API is in
  the `dora` profile, not `core`.
- **Grafana moves to 3300** (`GRAFANA_PORT=3300` in Obs's `.env`; Sure holds 3000), and
  `telemetry-generator` is not started.
- **The runner image has no pip.** `python -m pip` and `python -m venv` both fail in
  `ufawkes-ci`; use `uv venv` and `uv pip install` (the image ships `uv`).
- **Woodpecker is not needed for #220.** The real run uses a GitHub Actions workflow on the
  runner (`python-fawkes-path`, "DORA event (test environment)") and the Obs ingestion API.
  Pipe's own stack still needs a GitHub OAuth app.
- **Public repo, self-hosted runner.** The repo's fork-PR approval policy was
  `first_time_contributors`; it is now `all_external_contributors`.

## Rollback

`docker compose ... down` for the stack you started (never `down -v`); the old
Portainer and every existing stack are untouched.

## Upgrading Woodpecker (v3.15.0 to v3.20.1, #277)

v3.18.0 runs a database migration that alters log storage; it can be slow and is
one-way, so back up the `woodpecker_data` volume first. Do not pin v3.20.0: it
shipped an unintended breaking change (woodpecker-ci/woodpecker#7398).

```
cd ~/uFawkesPipe
docker compose stop woodpecker-server woodpecker-agent
docker run --rm -v ufawkespipe_woodpecker_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/woodpecker_data-v3.15.0.tgz -C /data .
git pull && docker compose up -d woodpecker-server woodpecker-agent
```

Check `docker compose logs woodpecker-server` for the migration, then run a pipeline.

**Rollback:** stop both services, restore the archive over the volume
(`docker run --rm -v ufawkespipe_woodpecker_data:/data -v "$PWD":/backup alpine sh -c 'rm -rf /data/* && tar xzf /backup/woodpecker_data-v3.15.0.tgz -C /data'`),
pin `v3.15.0` again in `compose.yaml`, and start the services. The archive holds
the database, so keep it until the new version has run a full pipeline.

# Plan: the `security` profile and the DefectDojo upload step work out of the box (#290)

`docker compose --profile security up` now gives a usable DefectDojo: Postgres 18 mounts at `/var/lib/postgresql`, nginx proxies to `defectdojo` (`DD_UWSGI_HOST`), and a one-shot `defectdojo-initializer` runs migrate, fixtures and admin-user creation, then pins the admin API token to `DOJO_API_TOKEN`. `defectdojo` and the celery services wait for it. Woodpecker step containers join the compose network (`WOODPECKER_BACKEND_DOCKER_NETWORK`), so the new default `defectdojo.url` (`http://defectdojo-nginx:8080`) is reachable. The generated `defectdojo-upload` step uses `auto_create_context=true`, fails on any non-201 import (after trying every report), and runs on `push` and `manual` on `main` including after a failed scan.

## Verification Strategy

| Criterion | Evidence |
|---|---|
| Upload step fails on a failed import, no `\|\| true` | `test_missing_report_skipped_but_failed_import_fails_step` |
| Product and engagement created | same test (`auto_create_context=true`) |
| Runs on `manual` and after a failed scan | `test_runs_on_main_push_and_manual_even_after_failed_scan` |
| Default URL is nginx | `test_default_url_is_nginx`; step network asserted by `test_standalone_agent_uses_default_network` |
| Compose still valid, images pinned | `make validate-docker`; `tests/unit/test_compose_yaml.py` |
| Initializer env and script names match the image | read from `defectdojo/defectdojo-django:2.38.0` (`/entrypoint-initializer.sh`, `/secret-file-loader.sh`) |
| Trivy import creates findings visible through the API | `tests/smoke/test_defectdojo_import.py` (needs `make up-security` and `DOJO_API_TOKEN`; skips otherwise). Not yet run against a live stack |
| Working `docker compose --profile security up` | Not yet run live; tracked on #290 |

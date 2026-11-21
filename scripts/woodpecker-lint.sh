#!/usr/bin/env bash
# Lint Woodpecker pipeline files with woodpecker-cli in Docker (#297).
# Usage: woodpecker-lint.sh FILE [FILE...]
#
# Files are copied into the container with `docker cp`, not bind-mounted. In CI the
# hook runs inside a job container, where $PWD is a path the host's Docker daemon
# cannot see, so a mount arrives empty and the CLI reports "no such file".
set -euo pipefail

IMAGE="woodpeckerci/woodpecker-cli:v3.20.1" # keep in step with compose.yaml
[ "$#" -gt 0 ] || {
  echo "usage: woodpecker-lint.sh FILE..." >&2
  exit 2
}

status=0
for file in "$@"; do
  name="$(basename "$file")"
  cid="$(docker create "$IMAGE" lint "/woodpecker/$name")"
  docker cp "$file" "$cid:/woodpecker/$name"
  docker start -a "$cid" || status=1
  docker rm -f "$cid" > /dev/null
done
exit "$status"

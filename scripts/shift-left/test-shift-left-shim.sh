#!/usr/bin/env bash
# scripts/shift-left/test-shift-left-shim.sh — shift-left.sh runs a tool from
# the uFawkesPipe clone a consumer repo pins in .pre-commit-config.yaml, with
# its arguments and stdin, and fails loudly when it can't.
set -euo pipefail

unset GIT_INDEX_FILE GIT_DIR GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR
cd "$(dirname "$0")/../.."
HERE="$PWD"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fails=0
check() { # check <description> <command...>
  local desc="$1"
  shift
  if "$@"; then echo "  ok   $desc"; else
    echo "  FAIL $desc"
    fails=$((fails + 1))
  fi
}
# shim <repo> [args...] -> $out, $rc (stdin "IN")
shim() {
  local repo="$1"
  shift
  out="$(cd "$repo" && printf 'IN' | bash "$HERE/scripts/shift-left/shift-left.sh" "$@" 2>&1)" && rc=0 || rc=$?
}

# pre-commit's cache: a clone of uFawkesPipe at the pinned rev, recorded in db.db.
export PRE_COMMIT_HOME="$TMP/pc-home"
mkdir -p "$PRE_COMMIT_HOME" "$TMP/clone/scripts/shift-left"
printf '#!/usr/bin/env bash\necho "from clone: args=$* stdin=$(cat)"\n' > "$TMP/clone/scripts/shift-left/echo-tool.sh"
chmod +x "$TMP/clone/scripts/shift-left/echo-tool.sh"
python3 -c 'import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); c.execute("create table repos (repo text not null, ref text not null, path text not null, primary key (repo, ref))"); c.commit()' "$PRE_COMMIT_HOME/db.db"
record() { python3 -c 'import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); c.execute("insert or replace into repos values (?, ?, ?)", sys.argv[2:]); c.commit()' "$PRE_COMMIT_HOME/db.db" "$@"; }

R="$TMP/consumer"
mkdir -p "$R"
git -C "$R" init -q
cat > "$R/.pre-commit-config.yaml" << 'YML'
repos:
  - repo: https://github.com/paruff/uFawkesPipe
    rev: v9.9.9
    hooks:
      - id: shift-left-stamp
YML

echo "From the pinned clone:"
record https://github.com/paruff/uFawkesPipe v9.9.9 "$TMP/clone"
shim "$R" echo-tool a b
check "runs the tool with its arguments and stdin" test "$out" = "from clone: args=a b stdin=IN"

echo "Not cloned yet:"
python3 -c 'import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); c.execute("delete from repos"); c.commit()' "$PRE_COMMIT_HOME/db.db"
mkdir -p "$TMP/bin"
cat > "$TMP/bin/pre-commit" << STUB
#!/usr/bin/env bash
[[ "\$1" == install-hooks ]] && python3 -c 'import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); c.execute("insert into repos values (?, ?, ?)", sys.argv[2:]); c.commit()' "$PRE_COMMIT_HOME/db.db" https://github.com/paruff/uFawkesPipe v9.9.9 "$TMP/clone"
STUB
chmod +x "$TMP/bin/pre-commit"
PATH="$TMP/bin:$PATH" shim "$R" echo-tool c
check "installs the hook environments, then runs it" test "$out" = "from clone: args=c stdin=IN"

echo "Failures are loud:"
shim "$R" no-such-tool
check "an unknown tool fails" test "$rc" -ne 0
check "and says which, at which rev" grep -q "no-such-tool.*v9.9.9" <<< "$out"
printf 'repos: []\n' > "$R/.pre-commit-config.yaml"
shim "$R" echo-tool
check "a repo that doesn't pin uFawkesPipe fails" test "$rc" -ne 0
check "and says so" grep -qi "ufawkespipe" <<< "$out"

echo "uFawkesPipe itself:"
mkdir -p "$R/scripts/shift-left"
printf '#!/usr/bin/env bash\necho "local copy"\n' > "$R/scripts/shift-left/echo-tool.sh"
chmod +x "$R/scripts/shift-left/echo-tool.sh"
shim "$R" echo-tool
check "a repo with its own scripts/shift-left runs those" test "$out" = "local copy"

cd "$HERE"
if [[ "$fails" -ne 0 ]]; then
  echo "test-shift-left-shim: $fails FAILED" >&2
  exit 1
fi
echo "test-shift-left-shim: all checks passed"

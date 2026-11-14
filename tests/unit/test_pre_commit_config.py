"""Regression tests for how .pre-commit-config.yaml provisions its hooks.

The Lint & Format job only runs if every hook installs. pre-commit installs a
remote Python hook by cloning its repository and running ``pip install .`` in a
fresh virtualenv, so a hook whose build downloads a binary fails whenever that
download does: shellcheck-py fetched the ShellCheck release while building and
an HTTP 504 took the whole job down (uFawkesPipe#208).

A hook that runs a tool the machine already has cannot fail that way, and
scripts/shift-left/require-tool.sh turns a missing tool into a loud failure
instead of a silent pass (docs/ai-sdlc/shift-left spec R4).
"""

import yaml


def _load_config(project_root):
    with open(project_root / ".pre-commit-config.yaml") as f:
        return yaml.safe_load(f) or {}


def _shellcheck_hooks(config):
    return [
        (repo, hook)
        for repo in config.get("repos") or []
        for hook in repo.get("hooks") or []
        if hook.get("id") == "shellcheck"
    ]


class TestShellcheckHook:
    """ShellCheck must not be built by pre-commit at hook-install time."""

    def test_configured_exactly_once(self, project_root):
        assert len(_shellcheck_hooks(_load_config(project_root))) == 1

    def test_does_not_build_a_remote_package(self, project_root):
        repo, _ = _shellcheck_hooks(_load_config(project_root))[0]
        assert repo["repo"] == "local", (
            "shellcheck must come from a hook this repo owns, not a remote "
            "repo whose environment pre-commit builds at install time"
        )

    def test_resolves_the_host_tool_loudly(self, project_root):
        _, hook = _shellcheck_hooks(_load_config(project_root))[0]
        entry = hook["entry"].split()
        assert entry[0].endswith("require-tool.sh"), (
            "a missing shellcheck must fail with an install hint, not pass silently"
        )
        assert entry[1] == "shellcheck"

    def test_keeps_warning_severity(self, project_root):
        _, hook = _shellcheck_hooks(_load_config(project_root))[0]
        assert "--severity=warning" in hook.get("args", [])

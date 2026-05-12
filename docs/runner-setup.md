# Runner Setup

This repo's CI runs on the org-level self-hosted runner `kizuna-stage-1`
(Linux x64). This page documents the runner-specific configuration the
workflows depend on so that future runners (or replacements) can be set
up to match.

## Runner identity

- Runner name: `kizuna-stage-1`
- OS: Linux (Hetzner-managed VM)
- Labels: `self-hosted`, `Linux`, `X64`, `build-hetzner`, `linux-kvm`
- Runner group: `linux-kvm-public` (visibility = selected)
- Org: `deep-thinking-llc`

Jobs target the runner via `runs-on: [self-hosted, Linux, build-hetzner]`.
The `build-hetzner` label is unique to this runner so future Linux runners
in other groups will not accidentally pick up these jobs.

## Repo access

The runner group is `visibility=selected`, so each repo that wants to use
the runner must be explicitly added. Add this repo with:

```
gh api -X PUT \
  /orgs/deep-thinking-llc/actions/runner-groups/4/repositories/<REPO_ID>
```

Or via the GitHub UI: **Org settings → Actions → Runner groups →
linux-kvm-public → Repository access**.

## Environment quirks the workflows compensate for

The runner runs the GitHub Actions agent as `root` inside a user
namespace, and that namespace strips a couple of capabilities that GNU
toolchains otherwise rely on. The CI workflows include these mitigations:

### 1. `TAR_OPTIONS=--no-same-owner`

The namespace restricts `CAP_CHOWN`, so any `tar -x` invocation that tries
to preserve archive ownership (which GNU tar does by default when running
as root) fails with `EPERM`. This breaks every action that downloads a
toolchain or cache via tarball — `actions/setup-*`, `jdx/mise-action`,
etc.

Setting `TAR_OPTIONS=--no-same-owner` at the workflow level makes GNU tar
skip the chown step on every extraction. This is the actual fix for this
runner's environment, not a workaround — every workflow that touches this
runner should keep this env set.

```yaml
env:
  TAR_OPTIONS: --no-same-owner
```

### 2. mise for toolchains, not `actions/setup-*`

Even with `TAR_OPTIONS` in place, the `actions/setup-*` family tries to
extract toolchains into the runner's shared `_tool/` cache directory.
That directory is owned by another user from a prior runner identity and
fails on write.

Switching to `mise` via `jdx/mise-action@v4` sidesteps this entirely:
mise installs toolchains under the runner user's home
(`~/.local/share/mise/`), which the runner user owns, so no permission
juggling is needed. Toolchain versions are pinned in `mise.toml` at the
repo root.

### 3. Python venv for PEP 668

The system Python on Debian/Ubuntu (Python 3.12+) is marked
`externally-managed` per PEP 668, so `pip install -e .` against system
Python fails. Workflows that install Python packages use a per-job
`python3 -m venv .venv` and run pip and pytest through `.venv/bin/`.

### 4. Local types-first install for the reference server

The reference server's `pyproject.toml` declares `oamp-types>=1.0.0` as a
PyPI dependency. On a clean CI checkout, that resolves to the **published**
PyPI release, which lags behind tip and lacks fields like `provenance`,
`governance`, and the top-level `metadata` on `KnowledgeStore`.

The server's install step installs the local `reference/python` package
first, in editable mode, so the in-tree types satisfy the requirement:

```yaml
.venv/bin/pip install -e ../python
.venv/bin/pip install -e ".[dev]"
```

## Adding a new runner

If you provision a replacement Linux runner:

1. Register it as an org-level runner.
2. Add it to a runner group with the repos that should use it.
3. Give it a unique custom label so jobs can target it precisely
   (`build-hetzner` is taken; pick something else).
4. Update `runs-on` in `.github/workflows/*.yml` if the label changes.
5. Verify the namespace constraints: if the runner runs as root inside
   a user namespace, keep `TAR_OPTIONS=--no-same-owner` in workflow env.
   If it runs as a non-root user with full caps, neither of these is
   needed.

If you provision a macOS runner alongside (the previous `clawd` setup),
add a separate `runs-on: [self-hosted, macOS]` job rather than expecting
one job to run on both. Labels do not act as a fallback.

## Secrets required for release.yml

`.github/workflows/release.yml` publishes packages to four registries
when a `v*.*.*` tag is pushed. The job needs these org-level or repo-level
secrets to be set:

| Secret | Used for | Where to obtain |
|---|---|---|
| `CRATES_IO_TOKEN` | `cargo publish` for `reference/rust` | <https://crates.io/settings/tokens> |
| `NPM_TOKEN` | `npm publish` for `reference/typescript` | <https://www.npmjs.com/settings/~/tokens> |
| `PYPI_TOKEN` | `twine upload` for `reference/python` | <https://pypi.org/manage/account/token/> |
| `HEX_TOKEN` | `mix hex.publish` for `reference/elixir` | <https://hex.pm/dashboard/keys> |

`GITHUB_TOKEN` is provided automatically by Actions and is used by
`softprops/action-gh-release` to create the GitHub release entry.

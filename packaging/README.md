# Packaging

Two ways to get Cropsmith:

| Method | For | Notes |
|---|---|---|
| **Standalone app** (`pyinstaller/`) | non-technical users | Download + run, no Python. Built per-OS in CI, attached to each release. |
| **pip / pipx** (PyPI) | anyone with Python | `pipx install cropsmith` -- one command, works on macOS / Linux / Windows. |

> Scoop and Homebrew were dropped: Homebrew can't build (opencv has no source
> distribution) and Scoop added nothing over pip, which is required regardless.
> Pip is the single package-manager path.

---

## pip / pipx

```bash
pipx install cropsmith        # isolated, on PATH, no venv juggling
# or
pip install cropsmith
```

Installs ~560 MB of runtime wheels. `web-to-pdf` additionally downloads a
Chromium browser (~90 MB) the first time it runs, into a shared user cache.

### Publishing (automated via GitHub Actions)

`.github/workflows/release.yml` builds and publishes to PyPI on any `v*` tag,
using **trusted publishing** (OIDC) -- no API token stored in the repo.

One-time setup on PyPI (https://pypi.org/manage/account/publishing/), add a
*pending publisher*:

| Field | Value |
|---|---|
| PyPI project name | `cropsmith` |
| Owner | `opieeipo` |
| Repository name | `cropsmith` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

Then cut a release:

```bash
git tag v0.3.0
git push origin v0.3.0     # CI builds wheels + standalone apps, publishes to PyPI
```

---

## Standalone app (PyInstaller)

See [`pyinstaller/`](pyinstaller/). Build locally:

```bash
pip install pyinstaller
cd packaging/pyinstaller
pyinstaller cropsmith.spec --noconfirm
# -> dist/cropsmith/cropsmith  (self-contained, no Python needed)
```

The release pipeline builds these for macOS / Windows / Linux and attaches the
zipped bundles to each GitHub release.

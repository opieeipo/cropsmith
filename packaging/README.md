# Packaging

Distribution manifests for installing `cropsmith` as a system-wide command.

| Method | Platform | Status |
|---|---|---|
| PyPI + `pipx` | all | **Recommended** -- single command, no clone |
| `scoop/cropsmith.json` | Windows (Scoop) | Ready to use |
| `homebrew/cropsmith.rb` | macOS / Linux (Homebrew) | Best-effort -- heavy deps make a pure formula impractical; prefer `pipx` |

---

## PyPI / pipx (recommended, any platform)

Once published to PyPI:

```bash
pipx install cropsmith        # isolated, on PATH, no venv juggling
# or
pip install cropsmith
```

### Publishing (automated via GitHub Actions)

`.github/workflows/release.yml` builds and publishes to PyPI on any `v*` tag,
using **trusted publishing** (OIDC) -- no API token is stored in the repo.

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
git tag v0.2.0
git push origin v0.2.0     # CI builds, publishes to PyPI, attaches artifacts
```

---

## Scoop (Windows)

The manifest builds an isolated virtualenv inside the Scoop app directory and
shims `cropsmith.exe`, so no global `pip` pollution.

Install directly from the raw manifest URL:

```powershell
scoop install https://raw.githubusercontent.com/opieeipo/cropsmith/main/packaging/scoop/cropsmith.json
```

Or, for updates via `scoop update`, host it in a bucket:

```powershell
scoop bucket add cropsmith https://github.com/opieeipo/cropsmith
scoop install cropsmith/cropsmith
```

Optional helper tools (used by some commands):

```powershell
scoop install ffmpeg tesseract ghostscript
```

---

## Homebrew (macOS / Linux)

Homebrew builds in a network-free sandbox, so every Python dependency must be
listed in the formula as a `resource`. Generate those once:

```bash
# Create a local tap and drop the formula in it
brew tap-new opieeipo/cropsmith
cp homebrew/cropsmith.rb "$(brew --repository)/Library/Taps/opieeipo/homebrew-cropsmith/Formula/"

# Auto-populate the `resource` blocks from pyproject.toml
brew update-python-resources opieeipo/cropsmith

# Install
brew install opieeipo/cropsmith
```

After install, fetch the Chromium browser used by `web-to-pdf`:

```bash
"$(brew --prefix)/opt/cropsmith/libexec/bin/playwright" install chromium
```

### Why the extra step?

Unlike Scoop (which installs on the user's machine with network access), a
Homebrew formula cannot reach PyPI during the build. `brew update-python-resources`
resolves and pins every dependency (with SHA256s) into the formula so the build
is reproducible and offline. It only needs to be re-run when dependencies change.

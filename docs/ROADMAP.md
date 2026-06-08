# Roadmap

## Now (shipping in 0.2.0)
- Friendly CLI: `web-to-pdf`, `shrink-pdf`, `merge-pdf`, `pdf-to-word`, `shrink-video`, `extract-text`
- Interactive `capture-pages` (draw a box, auto page-turn, OCR to searchable PDF)
- CI + release pipeline (build + publish to PyPI on tag via trusted publishing)
- Distribution: standalone apps (PyInstaller) + pip/pipx. (Scoop/Homebrew
  dropped -- brew can't build opencv from source, and pip is required anyway.)

## Right-click context-menu integration

Goal: invoke the **file-based** tools (`shrink-pdf`, `merge-pdf`, `pdf-to-word`,
`shrink-video`, `extract-text`) directly from the OS file manager's right-click
menu. (`web-to-pdf` / `capture-pages` are interactive and stay CLI-first.)

`cropsmith install-menu` / `uninstall-menu` registers the entries per platform.

### macOS -- Finder Quick Actions (Services) -- DONE
- Generates `*.workflow` Automator service bundles into `~/Library/Services/`,
  each running `cropsmith <command>` on the selected file(s), scoped by file type.
- Embeds the resolved absolute `cropsmith` path (GUI Services have no user PATH).
- Posts a notification on completion. Per-user, no admin rights.

### Windows -- Explorer context menu -- DONE (pending real-Windows verification)
- Registers `HKCU\Software\Classes\SystemFileAssociations\<.ext>\shell\Cropsmith.<cmd>`
  keys with `%1` for the selected file. Per-user (HKCU), no admin.
- Verbs auto-name their output (no `-o` needed), so each command is a single line.
- TODO: merge-pdf (multi-select) needs a DropTarget/shell extension; Win11
  top-level menu needs a packaged IExplorerCommand (currently legacy menu).

### Linux -- file-manager scripts / actions
- GNOME Files (Nautilus): scripts in `~/.local/share/nautilus/scripts/` or a
  Python extension.
- KDE Dolphin: `.desktop` ServiceMenus in `~/.local/share/kio/servicemenus/`.
- Thunar: custom actions via `uca.xml`.

### Open questions
- Single "Cropsmith" submenu vs. flat entries per action.
- Where outputs go: alongside source (`foo-min.pdf`) vs. a dialog/prompt.
- Bundling: context menu needs `cropsmith` reliably on PATH -> favors the
  PyPI/`pipx` install (absolute shim path) over a venv the user might move.

## Later
- Config file for default output naming / quality presets
- Drag-and-drop GUI wrapper
- Slim the standalone bundle further (opencv is the biggest un-earned weight;
  investigate OCR without opencv)

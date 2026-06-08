# Roadmap

## Now (shipping in 0.2.0)
- Friendly CLI: `web-to-pdf`, `shrink-pdf`, `merge-pdf`, `pdf-to-word`, `shrink-video`, `extract-text`
- Interactive `capture-pages` (draw a box, auto page-turn, OCR to searchable PDF)
- CI + release pipeline (build + publish to PyPI on tag via trusted publishing)
- Scoop manifest (working); Homebrew formula (see notes)

## Next: right-click context-menu integration

Goal: invoke the **file-based** tools (`shrink-pdf`, `merge-pdf`, `pdf-to-word`,
`shrink-video`, `extract-text`) directly from the OS file manager's right-click
menu. (`web-to-pdf` / `capture-pages` are interactive and stay CLI-first.)

The plan is an `cropsmith install-menu` / `uninstall-menu` command that registers
the right entries per platform:

### macOS -- Finder Quick Actions (Services)
- Generate `*.workflow` Automator service bundles into `~/Library/Services/`,
  each running `cropsmith <command>` on the selected file(s).
- Show up under right-click > Quick Actions. Scoped by file type (PDF, video).
- No admin rights needed; per-user install.

### Windows -- Explorer context menu
- Register `HKCU\Software\Classes\SystemFileAssociations\<.ext>\shell\Cropsmith.<cmd>`
  keys pointing at the `cropsmith` shim, with `%1` for the selected file.
- Per-user (HKCU), no admin. Submenu grouping via `SubCommands`/`MUIVerb`.
- Windows 11 cascading menu nuance: classic context menu is simplest first.

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
- Homebrew: revisit once heavy deps (opencv via pdf2docx, PyMuPDF) can be
  slimmed; `pipx` is the recommended macOS/Linux install until then.

"""Windows Explorer right-click integration via the per-user registry.

Adds entries under
``HKCU\\Software\\Classes\\SystemFileAssociations\\<ext>\\shell\\Cropsmith.<key>``
so each action only appears for the matching file type. Per-user (HKCU) -- no
admin rights needed.

Multi-select verbs (merge-pdf) are registered as **folder** actions instead --
right-click a folder (or inside it) and Cropsmith merges every PDF in that folder
(matching how the original mergePDF.py worked). This sidesteps the fact that a
classic per-file registry verb is invoked once per selected file.

Note: on Windows 11 these land in the legacy menu (right-click > "Show more
options"); the top-level Win11 menu requires a packaged IExplorerCommand.
"""

from __future__ import annotations

_BASE = r"Software\Classes\SystemFileAssociations"
_DIR = r"Software\Classes\Directory\shell"            # a selected folder (%1)
_DIR_BG = r"Software\Classes\Directory\Background\shell"  # empty space in a folder (%V)


def _delete_tree(root, path) -> bool:
    import winreg

    try:
        key = winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return False
    try:
        while True:
            try:
                sub = winreg.EnumKey(key, 0)
            except OSError:
                break
            _delete_tree(root, path + "\\" + sub)
    finally:
        winreg.CloseKey(key)
    try:
        winreg.DeleteKey(root, path)
        return True
    except OSError:
        return False


def _write_verb(winreg, key_path: str, title: str, exe: str, command: str) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, title)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{exe}"')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\command") as cmd:
        winreg.SetValueEx(cmd, "", 0, winreg.REG_SZ, command)


def _key_paths(action) -> list:
    """Registry key paths this action installs to (per-file ext, or folder)."""
    if action.multi:  # folder action: selected folder (%1) and folder background (%V)
        return [(rf"{_DIR}\Cropsmith.{action.key}", "%1"),
                (rf"{_DIR_BG}\Cropsmith.{action.key}", "%V")]
    return [(rf"{_BASE}\{ext}\shell\Cropsmith.{action.key}", "%1") for ext in action.exts]


def install(exe: str, progress) -> list:
    import winreg

    from . import ACTIONS

    installed = []
    for action in ACTIONS:
        for key_path, arg in _key_paths(action):
            _write_verb(winreg, key_path, action.title, exe, f'"{exe}" {action.verb} "{arg}"')
        installed.append(action.title)
        progress(f"Installed{' (folder)' if action.multi else ''}: {action.title}")
    progress("On Windows 11 these appear under right-click > 'Show more options'.")
    return installed


def uninstall(progress) -> list:
    import winreg

    from . import ACTIONS

    removed = []
    for action in ACTIONS:
        gone = False
        for key_path, _arg in _key_paths(action):
            if _delete_tree(winreg.HKEY_CURRENT_USER, key_path):
                gone = True
        if gone:
            removed.append(action.title)
            progress(f"Removed: {action.title}")
    return removed

"""Windows Explorer right-click integration via the per-user registry.

Adds entries under
``HKCU\\Software\\Classes\\SystemFileAssociations\\<ext>\\shell\\Cropsmith.<key>``
so each action only appears for the matching file type. Per-user (HKCU) -- no
admin rights needed.

Notes / limitations (v1):
* Multi-select verbs (merge-pdf) are skipped -- a classic registry verb is
  invoked once per selected file, so "merge all selected" needs a shell
  extension / DropTarget COM server. Tracked for a later pass.
* On Windows 11 these land in the legacy menu (right-click > "Show more
  options"); the top-level Win11 menu requires a packaged IExplorerCommand.
"""

from __future__ import annotations

_BASE = r"Software\Classes\SystemFileAssociations"


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


def install(exe: str, progress) -> list:
    import winreg

    from . import ACTIONS

    installed = []
    for action in ACTIONS:
        if action.multi:
            progress(f"Skipped (multi-select needs a shell extension): {action.title}")
            continue
        for ext in action.exts:
            key_path = rf"{_BASE}\{ext}\shell\Cropsmith.{action.key}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, action.title)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{exe}"')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\command") as cmd:
                winreg.SetValueEx(cmd, "", 0, winreg.REG_SZ, f'"{exe}" {action.verb} "%1"')
        installed.append(action.title)
        progress(f"Installed: {action.title}")
    progress("On Windows 11 these appear under right-click > 'Show more options'.")
    return installed


def uninstall(progress) -> list:
    import winreg

    from . import ACTIONS

    removed = []
    for action in ACTIONS:
        gone = False
        for ext in action.exts:
            key_path = rf"{_BASE}\{ext}\shell\Cropsmith.{action.key}"
            if _delete_tree(winreg.HKEY_CURRENT_USER, key_path):
                gone = True
        if gone:
            removed.append(action.title)
            progress(f"Removed: {action.title}")
    return removed

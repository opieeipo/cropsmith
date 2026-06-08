"""macOS Finder Quick Actions (Services) installer.

Generates one ``*.workflow`` bundle per action under ``~/Library/Services/``.
Each is an Automator "Run Shell Script" service that runs ``cropsmith <verb>`` on
the selected file(s) and posts a notification when done. Scoped by file type so,
e.g., the PDF actions only appear when PDFs are selected.
"""

from __future__ import annotations

import plistlib
import shutil
import subprocess
import uuid
from pathlib import Path

from . import ACTIONS

SERVICES_DIR = Path.home() / "Library" / "Services"


def _sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


_LOG_HEADER = (
    "#!/bin/bash\n"
    f"CROPSMITH={{cropsmith}}\n"
    'LOG="${{HOME:-/tmp}}/cropsmith-menu.log"\n'
    'exec >>"$LOG" 2>&1\n'
    "echo \"===== $(date '+%F %T') | {title} =====\"\n"
    'echo "exe: $CROPSMITH"\n'
    'echo "exe runnable: $([ -x "$CROPSMITH" ] && echo yes || echo NO)"\n'
    'echo "args: $*"\n'
)


def _script(action, exe: str) -> str:
    cropsmith = _sh_quote(exe)
    title = action.title.replace('"', '\\"')
    header = _LOG_HEADER.format(cropsmith=cropsmith, title=title)

    if action.multi:
        return (
            header
            + '[ "$#" -eq 0 ] && exit 0\n'
            'dir=$(dirname "$1")\n'
            'if "$CROPSMITH" merge-pdf "$@" -o "$dir/merged.pdf"; then\n'
            '  echo "OK -> $dir/merged.pdf"\n'
            f'  osascript -e \'display notification "Merged into merged.pdf" with title "Cropsmith" subtitle "{title}"\'\n'
            "else\n"
            '  echo "FAIL($?) merge"\n'
            f'  osascript -e \'display notification "Merge failed (see ~/cropsmith-menu.log)" with title "Cropsmith" subtitle "{title}"\'\n'
            "fi\n"
        )

    if action.out_ext:
        out_line = f'out="${{f%.*}}{action.out_suffix}{action.out_ext}"'
    else:  # keep the input extension
        out_line = f'out="${{f%.*}}{action.out_suffix}.${{f##*.}}"'

    return (
        header
        + "ok=0; fail=0\n"
        'for f in "$@"; do\n'
        f"  {out_line}\n"
        f'  if "$CROPSMITH" {action.verb} "$f" -o "$out"; then ok=$((ok+1)); echo "OK -> $out";'
        ' else rc=$?; fail=$((fail+1)); echo "FAIL($rc) on $f"; fi\n'
        "done\n"
        'echo "summary ok=$ok fail=$fail"\n'
        'if [ "$fail" -eq 0 ]; then\n'
        f'  osascript -e "display notification \\"$ok file(s) processed\\" with title \\"Cropsmith\\" subtitle \\"{title}\\""\n'
        "else\n"
        f'  osascript -e "display notification \\"$ok ok, $fail failed (see ~/cropsmith-menu.log)\\" with title \\"Cropsmith\\" subtitle \\"{title}\\""\n'
        "fi\n"
    )


def _u() -> str:
    return str(uuid.uuid4()).upper()


def _document_wflow(script: str) -> dict:
    return {
        "AMApplicationBuild": "523",
        "AMApplicationVersion": "2.10",
        "AMDocumentVersion": "2",
        "actions": [
            {
                "action": {
                    "AMAccepts": {
                        "Container": "List",
                        "Optional": False,
                        "Types": ["com.apple.cocoa.path"],
                    },
                    "AMActionVersion": "2.0.3",
                    "AMApplication": ["Automator"],
                    "AMParameterProperties": {
                        "COMMAND_STRING": {},
                        "CheckedForUserDefaultShell": {},
                        "inputMethod": {},
                        "shell": {},
                        "source": {},
                    },
                    "AMProvides": {
                        "Container": "List",
                        "Types": ["com.apple.cocoa.string"],
                    },
                    "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
                    "ActionName": "Run Shell Script",
                    "ActionParameters": {
                        "COMMAND_STRING": script,
                        "CheckedForUserDefaultShell": True,
                        "inputMethod": 1,  # 1 = pass selected files as arguments
                        "shell": "/bin/bash",
                        "source": "",
                    },
                    "BundleIdentifier": "com.apple.RunShellScript",
                    "CFBundleVersion": "2.0.3",
                    "CanShowSelectedItemsWhenRun": False,
                    "CanShowWhenRun": True,
                    "Category": ["AMCategoryUtilities"],
                    "Class Name": "RunShellScriptAction",
                    "InputUUID": _u(),
                    "Keywords": ["Shell", "Script", "Command", "Run", "Unix"],
                    "OutputUUID": _u(),
                    "UUID": _u(),
                    "UnlocalizedApplications": ["Automator"],
                    "arguments": {
                        "0": {"default value": 0, "name": "inputMethod", "required": "0",
                              "type": "0", "uuid": "0"},
                        "1": {"default value": "", "name": "source", "required": "0",
                              "type": "0", "uuid": "1"},
                        "2": {"default value": False, "name": "CheckedForUserDefaultShell",
                              "required": "0", "type": "0", "uuid": "2"},
                        "3": {"default value": "", "name": "COMMAND_STRING", "required": "0",
                              "type": "0", "uuid": "3"},
                        "4": {"default value": "/bin/sh", "name": "shell", "required": "0",
                              "type": "0", "uuid": "4"},
                    },
                    "isViewVisible": True,
                    "location": "309.000000:253.000000",
                    "nibPath": "/System/Library/Automator/Run Shell Script.action/Contents/Resources/main.nib",
                },
                "isViewVisible": True,
            }
        ],
        "connectors": {},
        "workflowMetaData": {
            "applicationBundleIDsByPath": {},
            "applicationPaths": [],
            "inputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "outputTypeIdentifier": "com.apple.Automator.nothing",
            "presentationMode": 11,
            "processesInput": 0,
            "serviceApplicationBundleID": "com.apple.finder",
            "serviceApplicationPath": "/System/Library/CoreServices/Finder.app",
            "serviceInputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": 0,
            "systemImageName": "NSActionTemplate",
            "useAutomaticInputType": 0,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }


def _info_plist(action) -> dict:
    return {
        "NSServices": [
            {
                "NSMenuItem": {"default": action.title},
                "NSMessage": "runWorkflowAsService",
                "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
                "NSSendFileTypes": action.utis,
            }
        ]
    }


def _bundle_path(action) -> Path:
    # Avoid ":" / "→" in the on-disk filename; keep them only in the menu title.
    return SERVICES_DIR / f"cropsmith-{action.key}.workflow"


def install(exe: str, progress) -> list:
    SERVICES_DIR.mkdir(parents=True, exist_ok=True)
    installed = []
    for action in ACTIONS:
        contents = _bundle_path(action) / "Contents"
        contents.mkdir(parents=True, exist_ok=True)
        with open(contents / "document.wflow", "wb") as fh:
            plistlib.dump(_document_wflow(_script(action, exe)), fh)
        with open(contents / "Info.plist", "wb") as fh:
            plistlib.dump(_info_plist(action), fh)
        installed.append(action.title)
        progress(f"Installed: {action.title}")
    _refresh(progress)
    return installed


def uninstall(progress) -> list:
    removed = []
    for action in ACTIONS:
        bundle = _bundle_path(action)
        if bundle.exists():
            shutil.rmtree(bundle)
            removed.append(action.title)
            progress(f"Removed: {action.title}")
    _refresh(progress)
    return removed


def _refresh(progress) -> None:
    """Ask the pasteboard server to re-scan Services so changes show up."""
    try:
        subprocess.run(["/System/Library/CoreServices/pbs", "-flush"], capture_output=True)
    except Exception:  # noqa: BLE001
        pass
    progress("Services menu refreshed (re-open Finder windows if needed).")

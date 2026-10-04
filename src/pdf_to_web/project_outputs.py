"""Project-local output locations and recoverable previous export snapshots."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def output_folder(root: Path) -> Path:
    root = root.resolve()
    folder = root / 'output'
    if folder.is_symlink():
        raise ValueError('Outputs must stay inside this project; the output folder must not be a symbolic link.')
    folder.resolve().relative_to(root)
    if folder.exists() and not folder.is_dir():
        raise ValueError('The project output location is not a folder.')
    for entry in folder.rglob('*'):
        if entry.is_symlink():
            raise ValueError('Outputs must stay inside this project; use ordinary files rather than symbolic links.')
    return folder


def preserve_previous_outputs(root: Path) -> Path | None:
    """Copy before replacement; never move or delete earlier exports."""
    folder = output_folder(root)
    entries = [p for p in folder.iterdir() if p.name != 'history' and not p.name.startswith('.') and p.name != 'image-drafts'] if folder.exists() else []
    if not entries:
        return None
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    snapshot = folder / 'history' / f'{stamp}-{uuid.uuid4().hex}'
    snapshot.mkdir(parents=True, exist_ok=False)
    try:
        for entry in entries:
            target = snapshot / entry.name
            if entry.is_dir():
                shutil.copytree(entry, target)
            else:
                shutil.copy2(entry, target)
    except OSError as exc:
        raise ValueError(f'Could not preserve previous exports in {snapshot}. No new export was started. Check folder permissions and free space: {exc}') from exc
    return snapshot


def output_locations(root: Path) -> dict[str, str]:
    return {'project_root': str(root.resolve()), 'output_root': str(output_folder(root))}


def open_output_folder(root: Path) -> Path:
    folder = output_folder(root)
    if not folder.is_dir():
        raise ValueError('Export files first; this project has no output folder yet.')
    try:
        if sys.platform == 'win32':
            os.startfile(str(folder))
        else:
            command = ['/usr/bin/open', str(folder)] if sys.platform == 'darwin' else ['xdg-open', str(folder)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
            if result.returncode:
                raise ValueError('The system file manager could not open the output folder. Use the displayed path.')
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('The system file manager is unavailable. Use the displayed output path.') from exc
    return folder

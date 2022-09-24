from pathlib import Path
from typing import Optional

from user_texts import add_files_info, change_files_info, delete_files_info


def git_output(
    add: Optional[list[Path]],
    delete: Optional[list[Path]],
    change: Optional[list[Path]],
):
    formatted = []

    if add:
        formatted.append(add_files_info)
        for fname in add:
            formatted.append(f"+ {fname}")

        formatted.append("")

    if delete:
        formatted.append(delete_files_info)
        for fname in delete:
            formatted.append(f"- {fname}")

        formatted.append("")

    if change:
        formatted.append(change_files_info)
        for i, fname in enumerate(change):
            formatted.append(f"{i} {fname}")

        formatted.append("")

    return "\n".join(formatted)

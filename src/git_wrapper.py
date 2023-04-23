import os
import subprocess
from pathlib import Path
from typing import Optional

import user_texts
from interactor import UserInput

DEFAULT_COMMIT_MESSAGE = "something changed"


class GitWrapper:
    def __init__(self, repo_path: Path):
        self.path = repo_path

    def show_changes(self) -> bool:
        untracked_files = self._get_untracked_files()
        combined_diff_output = self._get_combined_diff_output()

        changes = False
        if untracked_files:
            print(f"\n{user_texts.add_files_info}\n")
            for file in untracked_files:
                print(f"+ {file}")

            changes = True

        if combined_diff_output:
            print(f"\n{user_texts.change_files_info}\n")
            print(combined_diff_output)

            changes = True

        return changes

    def ensure_push(self, remote_name: Optional[str] = "origin", branch_name: Optional[str] = "main") -> None:
        local_commit_hash = self._get_commit_hash(branch_name)
        remote_commit_hash = self._get_remote_commit_hash(remote_name, branch_name)

        if local_commit_hash != remote_commit_hash:
            need_to_push = UserInput.ask_bool(user_texts.push_changes, default=True)
            if need_to_push:
                self._push_to_remote(remote_name, branch_name)

    def commit_and_push(self, remote_name: Optional[str] = "origin", branch_name: Optional[str] = "main"):
        commit_message = UserInput.raw(user_texts.commit_message, default=DEFAULT_COMMIT_MESSAGE)
        self.push(commit_message, remote_name, branch_name)

    def push(self, message: str, remote_name: Optional[str] = "origin", branch_name: Optional[str] = "main") -> None:
        self._stage_all_changes()
        self._create_commit(message)
        self._push_to_remote(remote_name, branch_name)

        print("Changes committed and pushed")

    def discard_changes(self) -> None:
        subprocess.run(["git", "checkout", "--", "."], cwd=self.path, check=True)

    def files(self) -> Path:
        excluded = (".git", ".gitignore")
        for dirpath, dirs, files in os.walk(self.path):
            dirs[:] = [d for d in dirs if d not in excluded]

            for filename in files:
                yield Path(os.path.join(dirpath, filename)).relative_to(self.path)

    def get_changed_files(self) -> list[tuple[str, Path]]:
        git_diff_files = subprocess.run(["git", "diff", "--name-status"], capture_output=True, text=True, cwd=self.path)
        git_untracked_files = subprocess.run(
            ["git", "ls-files", "--others"], capture_output=True, text=True, cwd=self.path
        )

        changed_files = []

        for line in git_diff_files.stdout.splitlines():
            status, file_path = line.split(maxsplit=1)
            if status != "D":  # Exclude deleted files
                changed_files.append((status, Path(file_path)))

        for line in git_untracked_files.stdout.splitlines():
            changed_files.append(("?", Path(line)))

        return changed_files

    def _get_untracked_files(self) -> list[str]:
        git_untracked_files = subprocess.run(
            ["git", "ls-files", "--others"], capture_output=True, text=True, cwd=self.path
        )
        return [line for line in git_untracked_files.stdout.splitlines()]

    def _get_combined_diff_output(self) -> str:
        git_diff_staged = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True, cwd=self.path)
        git_diff_unstaged = subprocess.run(["git", "diff"], capture_output=True, text=True, cwd=self.path)
        return git_diff_staged.stdout + git_diff_unstaged.stdout

    def _get_commit_hash(self, branch_name: str) -> str:
        return subprocess.run(
            ["git", "rev-parse", branch_name], cwd=self.path, check=True, text=True, stdout=subprocess.PIPE
        ).stdout.strip()

    def _get_remote_commit_hash(self, remote_name: str, branch_name: str) -> str:
        return (
            subprocess.run(
                ["git", "ls-remote", remote_name, branch_name],
                cwd=self.path,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            .stdout.strip()
            .split("\t")[0]
        )

    def _push_to_remote(self, remote_name: str, branch_name: str) -> None:
        subprocess.run(["git", "push", remote_name, branch_name], cwd=self.path, check=True)

    def _stage_all_changes(self) -> None:
        subprocess.run(["git", "add", "-A"], cwd=self.path, check=True)

    def _create_commit(self, message: str) -> None:
        subprocess.run(["git", "commit", "-m", message], cwd=self.path, check=True)

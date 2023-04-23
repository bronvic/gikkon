import filecmp
import os
import shutil
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import user_texts
from git_wrapper import GitWrapper
from interactor import UserInput
from validator import YES_VARIANTS

HOME = "home"
Paths = namedtuple("Paths", ["inner", "outer"])


def _select_files_to_revert(changed_files: list[tuple[str, Path]]) -> list[tuple[str, Path]]:
    print("\nSelect files to revert (use space-separated file numbers, press Enter for all, or type 'q' to quit):")
    for i, (_, file) in enumerate(changed_files, start=1):
        print(f"{i}. {file}")

    selected_indices = input("Enter file numbers, press Enter for all, or type 'q' to quit: ")

    if selected_indices.strip() == "":
        return changed_files
    elif selected_indices.lower() == "q":
        return []

    indices = [int(index) - 1 for index in selected_indices.split() if index.isdigit()]

    return [changed_files[i] for i in indices if 0 <= i < len(changed_files)]


def _copy(from_file: Path, to_file: Path) -> None:
    shutil.copy(from_file, to_file)


def _copy_file(src, dst):
    print(f"copying from {src} to {dst}")

    if not _has_write_access(dst):
        _copy_file_with_sudo(src, dst)
    else:
        _copy(src, dst)


def _copy_file_with_sudo(src, dst):
    print(f"copying from {src} to {dst}")
    try:
        subprocess.check_call(["sudo", "cp", src, dst])
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to copy file with sudo: {e}")
        sys.exit(1)


def _delete_file(file_path):
    print(f"removing {file_path}")
    if not _has_write_access(file_path):
        _delete_file_with_sudo(file_path)
    else:
        os.remove(file_path)


def _delete_file_with_sudo(file_path):
    try:
        subprocess.check_call(["sudo", "rm", file_path])
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to delete file with sudo: {e}")
        sys.exit(1)


def _has_write_access(file_path):
    return os.access(file_path, os.W_OK)


class Backuper:
    def __init__(self, path: Path, dry_run: bool = False) -> None:
        self.git = GitWrapper(path)
        self.dry_run = dry_run

    def add(self, fname: Path) -> None:
        fpath = fname.resolve()

        path = self.git.path.joinpath(Path(str(fpath)[1:]))
        if fpath.is_relative_to(Path.home()):
            path = self.git.path.joinpath(HOME, fpath.relative_to(Path.home()))

        if self.dry_run:
            if not path.parent.is_dir():
                print(f"Dry run: Creating directory {path.parent.resolve()}")

            print(f"Dry run: Copying {fpath} to {path}")
            return

        path.parent.mkdir(parents=True, exist_ok=True)

        _copy(fpath, path)

    def backup(self, ask_rollback: bool = True, delete_not_present=False) -> None:
        self.git.ensure_push()

        self._copy_files(delete_not_present)

        if self.git.show_changes():
            if self.dry_run:
                print("Dry run: commit and push changes")
                return

            if UserInput.ask_bool(user_texts.accept_changes, default=True):
                self.git.commit_and_push()
                return

            if ask_rollback and UserInput.ask_bool(user_texts.revert_changes, default=False):
                changed_files = self.git.get_changed_files()
                files_to_revert = _select_files_to_revert(changed_files)
                self.git.discard_changes()
                self._revert_files(files_to_revert)

            print("Abort changes")

    def print_files(self, print_all: bool, repo_paths: bool) -> None:
        filtered_files = [
            str(paths.inner) if repo_paths else str(paths.outer)
            for f in self.git.files()
            for paths in [self._absolute_paths_from_inner(f)]
            if (not repo_paths and paths.outer.is_file()) or (repo_paths and (print_all or paths.outer.is_file()))
        ]

        if not filtered_files:
            print("\nNo files under gikkon control")
        else:
            print("\nFiles under gikkon control:")
            for file_path in filtered_files:
                print(file_path)

    def _absolute_paths_from_inner(self, path: Path) -> Paths:
        str_path = str(path)

        outer_path = Path("/").joinpath(path)
        inner_path = self.git.path.joinpath(path)

        if str_path.startswith(HOME):
            outer_path = str.replace(str_path, f"{HOME}/", "")
            outer_path = Path.home().joinpath(Path(outer_path))

        return Paths(inner=inner_path, outer=outer_path)

    def _copy_files(self, delete_not_present=False) -> None:
        for inner_path in self.git.files():
            paths = self._absolute_paths_from_inner(inner_path)

            if delete_not_present and not paths.outer.exists():
                ok = input(f"Delete {paths.inner} [y/N]? ").lower()
                if ok in YES_VARIANTS:
                    _delete_file(paths.inner)

            if paths.outer.exists() and paths.outer.is_file():
                if not filecmp.cmp(paths.outer, paths.inner):
                    _copy(paths.outer, paths.inner)

    def _revert_files(self, files: list[tuple[str, Path]]) -> None:
        for status, file in files:
            inner_path, outer_path = self._absolute_paths_from_inner(Path(file))

            if status == "?":
                _delete_file(inner_path)
            else:
                _copy_file(inner_path, outer_path)

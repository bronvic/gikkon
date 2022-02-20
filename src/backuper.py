import filecmp
import os
import shutil
from collections import namedtuple
from pathlib import Path

from git_saver import Git
from wrappers import DryRunnable, maybe_dry

HOME = "home"


Pathes = namedtuple("Pathes", ["inner", "outer"])


class Backuper(DryRunnable):
    def __init__(
        self, path: Path, delete_unpresent: bool = False, dry_run: bool = False
    ) -> None:
        self.git = Git(path, dry_run)
        self.delete_unpresent = delete_unpresent

        super().__init__(dry_run)

    def backup(self) -> None:
        self.save_to_git()
        self.git.push_to_repo()

    def add(self, fname: Path) -> None:
        fpath = fname.resolve()

        path = self.git.path.joinpath(Path(str(fpath)[1:]))
        if fpath.is_relative_to(Path.home()):
            path = self.git.path.joinpath(HOME, fpath.relative_to(Path.home()))

        path.parent.mkdir(parents=True, exist_ok=True)

        self.copy(fpath, path)

    def commit(self) -> None:
        self.git.push_to_repo()

    def print_files(self, print_all: bool, repo_pathes: bool) -> None:
        print("\nFiles under gikkon controll:")
        for f in self.files():
            pathes = self.absolute_pathes_from_inner(f)

            if not repo_pathes and not pathes.outer.is_file():
                continue

            if repo_pathes and not print_all and not pathes.outer.is_file():
                continue

            print(str(pathes.inner)) if repo_pathes else print(str(pathes.outer))

    def save_to_git(self) -> None:
        for inner_path in self.files():
            pathes = self.absolute_pathes_from_inner(inner_path)

            # delete files which presents in git, but not in the system
            # if --delete option is True
            if self.delete_unpresent and not pathes.outer.exists():
                ok = input(f"Delete {pathes.inner} [y/N]? ")
                if ok in ("Y", "y", "yes"):
                    self.delete(pathes.inner)

            if pathes.outer.exists() and pathes.outer.is_file():
                if not filecmp.cmp(pathes.outer, pathes.inner):
                    self.copy(pathes.outer, pathes.inner)

    # return: inner, outer
    def absolute_pathes_from_inner(self, path: Path) -> Pathes:
        str_path = str(path)

        outer_path = Path("/").joinpath(path)
        inner_path = self.git.path.joinpath(path)

        if str_path.startswith(HOME):
            outer_path = str.replace(str_path, f"{HOME}/", "")
            outer_path = Path.home().joinpath(Path(outer_path))

        return Pathes(inner=inner_path, outer=outer_path)

    @maybe_dry
    def delete(self, fpath: Path) -> None:
        print(f"deleting {fpath}")

        fpath.unlink(missing_ok=True)

    @maybe_dry
    def copy(self, from_file: Path, to_file: Path) -> None:
        print(f"copying from {from_file} to {to_file}")

        shutil.copy(from_file, to_file)

    def files(self) -> Path:
        # Exclude .git files from backuping
        excluded = (".git", ".gitignore")
        for dirpath, dirs, files in os.walk(self.git.path):
            dirs[:] = [d for d in dirs if not d in excluded]

            for filename in files:
                yield Path(os.path.join(dirpath, filename)).relative_to(self.git.path)
